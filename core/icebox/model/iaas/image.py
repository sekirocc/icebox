from icebox import model
import json
import datetime

from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from densefog.model.job import job as job_model

from icebox import config
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import waiter
from icebox.model.project import project as project_model
from icebox.model.iaas.openstack import image as image_provider
from icebox.model.iaas.openstack import api as op_api

from densefog import logger
logger = logger.getChild(__file__)

WAIT_CAPSHOT_TIMEOUT = 600
WAIT_SNAPSHOT_TIMEOUT = 300

PUBLIC_IMAGE = utils.encode_uuid(
    '00000000-0000-0000-0000-000000000000')

PLATFORM_UNKNOWN = 'unknown'
PLATFORM_LINUX = 'linux'
PLATFORM_WINDOWS = 'windows'

OS_UNKNOWN = 'unknown'
OS_UBUNTU = 'ubuntu'
OS_CENTOS = 'centos'
OS_DEBIAN = 'debian'
OS_FEDORA = 'fedora'
OS_WINDOWS = 'windows'

PROCESSOR_TYPE_32 = '32'
PROCESSOR_TYPE_64 = '64'
PROCESSOR_TYPE_UNKNOWN = 'unknown'

IMAGE_STATUS_PENDING = 'pending'
IMAGE_STATUS_ACTIVE = 'active'
IMAGE_STATUS_DELETED = 'deleted'
IMAGE_STATUS_CEASED = 'ceased'
IMAGE_STATUS_ERROR = 'error'

IMAGE_STATUS_MAP = {
    image_provider.IMAGE_STATUS_ACTIVE: IMAGE_STATUS_ACTIVE,
    image_provider.IMAGE_STATUS_QUEUED: IMAGE_STATUS_PENDING,
    image_provider.IMAGE_STATUS_SAVING: IMAGE_STATUS_PENDING,
    image_provider.IMAGE_STATUS_PENDING_DELETE: IMAGE_STATUS_DELETED,
    image_provider.IMAGE_STATUS_KILLED: IMAGE_STATUS_DELETED,
    image_provider.IMAGE_STATUS_DELETED: IMAGE_STATUS_DELETED,
}


class Image(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.image

    def status_deletable(self):
        return self['status'] in [
            IMAGE_STATUS_ACTIVE,
            IMAGE_STATUS_ERROR,
        ]

    def format(self):
        formated = {
            'imageId': self['id'],
            'projectId': self['project_id'],
            'name': self['name'],
            'description': self['description'],
            'size': self['size'],
            'platform': self['platform'],
            'osFamily': self['os_family'],
            'processorType': self['processor_type'],
            'minVcpus': self['min_vcpus'],
            'minMemory': self['min_memory'],
            'minDisk': self['min_disk'],
            'status': self['status'],
            'isPublic': self['project_id'] == PUBLIC_IMAGE,
            'updated': self['updated'],
            'created': self['created'],
            'deleted': self['deleted'],
            'ceased': self['ceased'],
        }
        if formated['isPublic']:
            formated['projectId'] = None
        return formated


def create(project_id, instance_id, name=''):
    logger.info('.create() start.')
    from icebox.model.iaas import instance as instance_model

    instance = instance_model.get(instance_id)
    instance.must_be_available()
    # TODO. instance should lock??

    if not instance.boot_from_volume():
        raise iaas_error.InstanceCreateImageUnsupported(instance['id'])

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        project.must_have_enough_quota('images', 1)
        # assume creation success.
        project.consume_quota('images', 1)

    image_id = 'img-%s' % utils.generate_key(8)

    # some attributes inherit from instance's image
    instance_image = get(instance['image_id'])
    # dummy id, we didnot create image in openstack yet.
    dummy_id = 'dummy-' + utils.generate_key(18)

    Image.insert(**{
        'id': image_id,
        'op_image_id': dummy_id,
        'project_id': project_id,
        'name': name,
        'description': '',
        'size': 0,
        'platform': instance_image['platform'],
        'os_family': instance_image['os_family'],
        'processor_type': instance_image['processor_type'],
        'min_vcpus': instance_image['min_vcpus'],
        'min_memory': 0,
        'min_disk': 0,
        'status': IMAGE_STATUS_PENDING,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })

    # schedule a CaptureInstances job to sync instance status
    instance_model.Instance.update(instance_id, **{
        'status': instance_model.INSTANCE_STATUS_SCHEDULING,
        'updated': datetime.datetime.utcnow(),
    })
    model.actions_job('CaptureInstances',
                      project_id,
                      [instance_id],
                      [])

    # it takes long time, so schedule a job.
    job = job_model.create(
        action='CreateImage',
        project_id=project_id,
        try_max=1,
        try_period=config.CONF.try_period,
        params={
            'args': {'image_id': image_id, 'instance_id': instance_id},
            'resource_ids': [image_id]  # for response.
        }
    )

    logger.info('.create() OK.')

    return job


@utils.footprint(logger)
def create_image(image_id, instance_id):
    """
    step 0: invoke nova create_image, to get the boot volume's snapshot
    step 1: create capshot from the snapshot, and wait it available,
    step 3: create another image
    step 4. update location of the new image.
    step 5: delete old image, delete boot volume's snapshot.
    step 6. save image size.
    """
    from icebox.model.iaas import instance as instance_model

    image = get(image_id)
    instance = instance_model.get(instance_id)
    project = project_model.get(image['project_id'])

    try:
        nova_image = op_api.do_nova_create_image(project['op_project_id'],
                                                 instance['op_server_id'],
                                                 'safe-delete')
        nova_image_id = nova_image['id']
        min_disk = nova_image['min_disk']
        min_memory = nova_image['min_memory']

        # it must contains block_device_mapping
        bdm = json.loads(nova_image['block_device_mapping'])
        assert len(bdm) == 1, ('no block device mapping in nova create_image!'
                               'abort create_image')
        nova_snapshot_id = bdm[0]['snapshot_id']

        waiter.wait_snapshot_available(nova_snapshot_id,
                                       timeout=WAIT_SNAPSHOT_TIMEOUT)

        op_capshot = op_api.do_create_capshot(project['op_project_id'],
                                              nova_snapshot_id)
        op_capshot = waiter.wait_capshot_available(
            op_capshot['id'], timeout=WAIT_CAPSHOT_TIMEOUT)

        # use icebox image id as openstack image name
        op_image = op_api.do_glance_create_image(
            project_id=project['op_project_id'],
            name=image_id,
            min_disk=min_disk,
            min_memory=min_memory,
            capshot_id=op_capshot['id'],
            location=op_capshot['provider_location'])

    except Exception:
        # after silently clean up, re-raise current exception
        with utils.defer_reraise():

            # delete nova create image
            # delete nova create snapshot
            # delete capshot
            # delete glance create image
            with utils.silent():
                op_api.do_delete_image(nova_image_id)

            with utils.silent():
                op_api.do_delete_snapshot(nova_snapshot_id)

            with utils.silent():
                op_api.do_delete_capshot(op_capshot['id'])

            with utils.silent():
                op_api.do_delete_image(op_image['id'])

    # try your best to delete the old image.
    with utils.silent(lambda ex: logger.trace(ex)):
        op_api.do_delete_image(nova_image_id)

    # try your best to delete the boot volume's snapshot, we don't need it now.
    with utils.silent(lambda ex: logger.trace(ex)):
        op_api.do_delete_snapshot(nova_snapshot_id)

    # update image with new create op_image.
    # TODO, min_disk, min_memory really?
    Image.update(image_id, **{
        'op_image_id': op_image['id'],
        'status': IMAGE_STATUS_ACTIVE,
        'size': op_capshot['size'] * (1024 ** 3),  # unit: GB => B
        'min_disk': min_disk,
        'min_memory': min_memory,
        'updated': datetime.datetime.utcnow(),
    })


@utils.footprint(logger)
def create_image_failed(image_id):
    """
    Callback for create_image failed. mark image error
    """
    Image.update(image_id, **{
        'status': IMAGE_STATUS_ERROR,
        'updated': datetime.datetime.utcnow(),
    })


def _pre_delete(project_id, image_ids):
    from icebox.model.iaas import instance as instance_model

    instances = instance_model.limitation(image_ids=image_ids)['items']

    alive_instances = []
    for instance in instances:
        if not instance.is_deleted():
            alive_instances.append(instance['id'])
    if alive_instances:
        raise iaas_error.DeleteImagesWhenInstanceExists(alive_instances)

    images = []
    for image_id in image_ids:
        with base.lock_for_update():
            image = get(image_id)

        image.must_belongs_project(project_id)
        if not image.status_deletable():
            raise iaas_error.ImageCanNotDelete(image_id)

        images.append(image)

    return images


@base.transaction
def delete(project_id, image_ids):
    logger.info('.delete() start. total count: %s, image_ids: %s' %
                (len(image_ids), image_ids))

    images = _pre_delete(project_id, image_ids)

    for image in images:
        Image.update(image['id'], **{
            'status': IMAGE_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    # manage api could delete public images withou a project model.
    # but public api should have a project model, and release project quota.
    if project_id != PUBLIC_IMAGE:
        logger.debug('they are project\'s private images, release quota for project')   # noqa
        with base.lock_for_update():
            project = project_model.get(project_id)

        project.release_quota('images', len(images))

    logger.info('.delete() OK.')

    # create a job that will execute very later.
    # because erase a image from openstack required its instances all erased.
    job_model.create(
        action='EraseImages',
        params={
            'resource_ids': image_ids
        },
        run_at=utils.seconds_later(config.CONF.erase_delay * 2),
        try_period=config.CONF.try_period * 4)


def get(image_id):
    logger.info('.get() start. image: %s' % image_id)
    image = Image.get_as_model(image_id)
    if image is None:
        raise iaas_error.ImageNotFound(image_id)
    logger.info('.get() OK.')
    return image


def limitation(image_ids=None, project_ids=None, is_public=False, status=None,
               search_word=None, offset=0, limit=10, reverse=True):
    """
    if is_public, return paged public images.
    if is not public, then return project_ids's private images.
    if neither public nor project_ids is passed in,
        then return paged images with a few filters,
        like search_word, status, etc..
    """
    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, image_ids)

        select_projects = [PUBLIC_IMAGE] if is_public else project_ids
        _where = filters.filter_project_ids(_where, t, select_projects)

        _where = filters.filter_status(_where, t, status)
        _where = filters.filter_search_word(_where, t, search_word)
        return _where

    logger.info('.limitation() start')
    logger.info('project_ids: %s, is_public: %s' % (project_ids, is_public))
    page = Image.limitation_as_model(where,
                                     limit=limit,
                                     offset=offset,
                                     order_by=filters.order_by(reverse))

    logger.info('.limitation() OK. get images: %s' % len(page['items']))

    return page


def sync(image_id):
    """
    image sync api need not argument image_id. but for identical with other
    resources' sync api. we accept image_id here.
    """
    logger.info('.sync() start, image_id (%s)' % image_id)

    image = get(image_id)
    if image.is_deleted():
        logger.info('image is already deleted, skip it.')
        return image

    op_image_id = image['op_image_id']

    try:
        op_image = op_api.do_get_image(op_image_id)
    except:
        Image.update(image_id, **{
            'status': IMAGE_STATUS_ERROR,
            'updated': datetime.datetime.utcnow(),
        })
        raise

    logger.info('provider image status (%s).' % op_image['status'])

    image_status = IMAGE_STATUS_MAP[op_image['status']]
    min_memory = op_image['min_memory']
    min_disk = op_image['min_disk']
    size = op_image['size']

    logger.info('image (%s) status: (%s) => (%s).' %
                (image['id'], image['status'], image_status))

    logger.info('image min_memory: %s, min_disk: %s, size: %s' %
                (min_memory, min_disk, size))

    Image.update(image_id, **{
        'min_memory': min_memory,
        'min_disk': min_disk,
        'size': size,
        'status': image_status,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.sync() OK.')

    image = get(image_id)
    return image


def sync_all():
    logger.info('.sync_all() start')

    op_images = op_api.do_list_images()
    for op_image in op_images:
        image_status = IMAGE_STATUS_MAP[op_image['status']]

        image = Image.first(lambda t: t['op_image_id'] == op_image['id'])
        if image:
            logger.info('provider image exists in db image, '
                        'update db status')
            logger.info('image status: (%s) => (%s)' % (
                        image['status'], image_status))

            Image.update(image['id'], **{
                'min_memory': op_image['min_memory'],
                'min_disk': op_image['min_disk'],
                'status': image_status,
            })
        else:
            logger.info('provider image doesnt exists in db image, '
                        'insert db.')
            logger.info('image status: (None) => (%s)' % image_status)
            Image.insert(**{
                'id': 'img-%s' % utils.generate_key(8),
                'op_image_id': op_image['id'],
                'name': op_image['name'],
                'project_id': PUBLIC_IMAGE,
                'description': '',
                'size': op_image['size'],
                'platform': PLATFORM_UNKNOWN,
                'os_family': OS_UNKNOWN,
                'processor_type': PROCESSOR_TYPE_UNKNOWN,
                'min_vcpus': 1,
                'min_memory': op_image['min_memory'],
                'min_disk': op_image['min_disk'],
                'status': image_status,
                'updated': datetime.datetime.utcnow(),
                'created': datetime.datetime.utcnow(),
            })

        logger.info('.sync_all() OK.')


def modify(project_id, image_id, name=None, description=None,
           os_family=None, platform=None, processor_type=None):
    """
    modify images. name & description
    """
    logger.info('.modify() start')
    image = get(image_id)

    if project_id:
        image.must_belongs_project(project_id)
    elif image['project_id'] != PUBLIC_IMAGE:
        raise iaas_error.ImageCanNotModify(
            image_id,
            'Can not modify project\'s private image through manage api.')

    if name is None:
        name = image['name']

    if description is None:
        description = image['description']

    if os_family is None:
        os_family = image['os_family']

    if platform is None:
        platform = image['platform']

    if processor_type is None:
        processor_type = image['processor_type']

    Image.update(image_id, **{
        'name': name,
        'description': description,
        'os_family': os_family,
        'platform': platform,
        'processor_type': processor_type,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')

    return image_id


@utils.footprint(logger)
def erase(image_id):
    """
    step 1. find capshot
    step 2. if capshot exists. then the image is built from capshot
            delete capshot first
    step 3. delete image.
    """
    logger.info('erase image: %s' % image_id)

    image = get(image_id)
    if image['ceased'] is not None:
        logger.warn('image is already ceased before.')
        return
    if image['status'] != IMAGE_STATUS_DELETED:
        logger.warn('image status is not DELETED, can not be ceased!')
        return

    if (image['op_image_id'] and
       not image['op_image_id'].startswith('dummy')):
        op_image = op_api.do_get_image(image['op_image_id'])
        op_capshot_id = op_image['capshot_id']

        op_api.do_delete_image(image['op_image_id'])
        if op_capshot_id:
            # if image is built from capshot. delete_image will delete
            # rbd image instantly. we should tolerant delete
            # capshot failed. actually it's openstack delete_capshot
            # should tolerant the failure.
            with utils.silent():
                op_api.do_delete_capshot(op_capshot_id)

    Image.update(image_id, **{
        'status': IMAGE_STATUS_CEASED,
        'ceased': datetime.datetime.utcnow(),
    })
