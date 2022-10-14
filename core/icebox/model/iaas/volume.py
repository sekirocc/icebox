from icebox import model
import datetime

from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from densefog.model.job import job as job_model

from icebox import config
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import instance_volume as instance_volume_model

from icebox.model.iaas.openstack import block as block_provider
from icebox.model.iaas.openstack import api as op_api
from icebox.model.project import project as project_model

from densefog import logger
logger = logger.getChild(__file__)

VOLUME_STATUS_PENDING = 'pending'
VOLUME_STATUS_ACTIVE = 'active'
VOLUME_STATUS_ATTACHING = 'attaching'
VOLUME_STATUS_DETACHING = 'detaching'

VOLUME_STATUS_IN_USE = 'inuse'
VOLUME_STATUS_BACKING_UP = 'backup_ing'
VOLUME_STATUS_RESTORING_BACKUP = 'backup_restoring'
VOLUME_STATUS_DELETED = 'deleted'
VOLUME_STATUS_CEASED = 'ceased'
VOLUME_STATUS_ERROR = 'error'

VOLUME_STATE_MAP = {
    block_provider.VOLUME_STATUS_CREATING: VOLUME_STATUS_PENDING,
    block_provider.VOLUME_STATUS_EXTENDING: VOLUME_STATUS_PENDING,
    block_provider.VOLUME_STATUS_DETACHING: VOLUME_STATUS_DETACHING,
    block_provider.VOLUME_STATUS_AVAILABLE: VOLUME_STATUS_ACTIVE,
    block_provider.VOLUME_STATUS_ATTACHING: VOLUME_STATUS_ATTACHING,
    block_provider.VOLUME_STATUS_IN_USE: VOLUME_STATUS_IN_USE,
    block_provider.VOLUME_STATUS_DELETING: VOLUME_STATUS_DELETED,
    block_provider.VOLUME_STATUS_BACKING_UP: VOLUME_STATUS_BACKING_UP,
    block_provider.VOLUME_STATUS_RESTORING_BACKUP: VOLUME_STATUS_RESTORING_BACKUP,  # noqa

    block_provider.VOLUME_STATUS_ERROR: VOLUME_STATUS_ERROR,
    block_provider.VOLUME_STATUS_ERROR_DELETING: VOLUME_STATUS_ERROR,
    block_provider.VOLUME_STATUS_ERROR_RESTORING: VOLUME_STATUS_ERROR,
    block_provider.VOLUME_STATUS_ERROR_EXTENDING: VOLUME_STATUS_ERROR,
}

SUPPORTED_VOLUME_TYPES = ["normal"]

VOLUME_TYPES_MAP = {
    'normal': 'sata',
    'performance': 'ssd',
}

OP_VOLUME_TYPES_MAP = {
    'sata': 'normal',
    'ssd': 'performance',
}


class Volume(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.volume

    def status_deletable(self):
        return self['status'] in [
            VOLUME_STATUS_ACTIVE,
            VOLUME_STATUS_ERROR
        ]

    def status_attachable(self):
        return self['status'] in [VOLUME_STATUS_ACTIVE]

    def status_detachable(self):
        return self['status'] in [VOLUME_STATUS_IN_USE]

    def status_extendable(self):
        return self['status'] in [VOLUME_STATUS_ACTIVE]

    def format(self):
        formated = {
            'volumeId': self['id'],
            'volumeType': self['volume_type'],
            'projectId': self['project_id'],
            'name': self['name'],
            'description': self['description'],
            'size': self['size'],
            'status': self['status'],
            'updated': self['updated'],
            'created': self['created'],
            'deleted': self['deleted'],
            'ceased': self['ceased'],
        }
        try:
            formated['instanceId'] = self['instance_id']
        except:
            formated['instanceId'] = None

        return formated


def _pre_create(project, size, volume_type, snapshot_id, count):
    if not snapshot_id and not (size and volume_type):
        raise iaas_error.VolumeCreateParamError()

    op_snapshot_id = None
    if snapshot_id:
        from icebox.model.iaas import snapshot as snapshot_model
        with base.lock_for_update():
            snapshot = snapshot_model.get(snapshot_id)

        snapshot.must_be_available()

        op_snapshot_id = snapshot['op_snapshot_id']
        # prefer size & volume_type in snapshot
        size = snapshot['size']
        volume_type = snapshot['volume_type']

    volume_type = volume_type.lower()
    # check volume_type
    if volume_type not in SUPPORTED_VOLUME_TYPES:
        raise iaas_error.VolumeCreateVolumeTypeNotSupportError()

    project.must_have_enough_quotas(volumes=count,
                                    volume_size=count * size)

    return size, volume_type, op_snapshot_id


def create(project_id,
           size=None, volume_type=None, snapshot_id=None,
           name='', count=1):
    """
    create a volume with size and volume_type

    #  combo 1. create by size & volume_type
    #  combo 2. create by snapshot.

    async job
    """
    logger.info('.create() begin, total count: %s' % count)

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        size, volume_type, op_snapshot_id = _pre_create(project,
                                                        size,
                                                        volume_type,
                                                        snapshot_id,
                                                        count)
        # assume all creation success
        project.consume_quotas(volumes=count,
                               volume_size=count * size)

    op_project_id = project['op_project_id']
    op_volume_type = VOLUME_TYPES_MAP[volume_type]

    creatings = []
    exceptions = []
    for i in range(count):
        volume_id = 'v-%s' % utils.generate_key(8)

        try:
            op_volume = op_api.do_create_data_volume(
                size=size,
                # use icebox model id as openstack resource name
                name=volume_id,
                op_project_id=op_project_id,
                volume_type=op_volume_type,
                snapshot_id=op_snapshot_id)

        except Exception as ex:
            exceptions.append({
                'volume': None,
                'exception': ex
            })
            continue

        volume_id = Volume.insert(**{
            'id': volume_id,
            'op_volume_id': op_volume['id'],
            'volume_type': OP_VOLUME_TYPES_MAP[op_volume['volume_type']],  # noqa
            'project_id': project_id,
            'name': name,
            'description': '',
            'size': size,
            'status': VOLUME_STATUS_PENDING,
            'updated': datetime.datetime.utcnow(),
            'created': datetime.datetime.utcnow(),
        })
        creatings.append(volume_id)

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)
        # release those exceptions quotas
        project.release_quotas(volumes=len(exceptions),
                               volume_size=len(exceptions) * size)

    logger.info('.create() OK. creatings: %s, exceptions: %s' %
                (len(creatings), len(exceptions)))

    return model.actions_job('CreateVolumes',
                             project_id,
                             creatings,
                             exceptions)


def _pre_delete(project_id, volume_ids):
    """
    Preconditions
        Volume status must be available, in-use, error, or error_restoring.
        You cannot already have a snapshot of the volume.
        You cannot delete a volume that is in a migration.
    """
    volumes = []
    for volume_id in volume_ids:
        with base.lock_for_update():
            volume = get(volume_id)

        volume.must_belongs_project(project_id)

        if not volume.status_deletable():
            raise iaas_error.VolumeCanNotDelete(volume_id)

        volumes.append(volume)
    return volumes


@base.transaction
def delete(project_id, volume_ids):
    """
    delete volumes.
    """
    logger.info('.delete() begin, total count: %s, volume_ids: %s' %
                (len(volume_ids), volume_ids))

    with base.lock_for_update():
        project = project_model.get(project_id)

    volumes = _pre_delete(project_id, volume_ids)
    for volume in volumes:
        Volume.update(volume['id'], **{
            'status': VOLUME_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    qt_volumes = len(volumes)
    qt_volume_size = sum([int(v['size']) for v in volumes])

    project.release_quotas(volumes=qt_volumes,
                           volume_size=qt_volume_size)

    logger.info('.delete() OK.')
    job_model.create(
        action='EraseVolumes',
        params={
            'resource_ids': volume_ids
        },
        run_at=utils.seconds_later(config.CONF.erase_delay),
        try_period=config.CONF.try_period)


def _pre_attach(project_id, volume_ids, instance_id):
    """
    check pre-conditions before attaching.

    Preconditions
        instance should be 'active' or 'stopped';
        volumes should be 'available'

    if status are inappropriate, raise exception
    else return instance and volumes models.
    """
    with base.lock_for_update():
        instance = instance_model.get(instance_id)

    instance.must_belongs_project(project_id)

    if not instance.status_attachable():
        raise iaas_error.InstanceCanNotBeAttached(instance_id)

    volumes = []
    for volume_id in volume_ids:
        with base.lock_for_update():
            volume = get(volume_id)

        volume.must_belongs_project(project_id)

        if not volume.status_attachable():
            raise iaas_error.VolumeCanNotAttach(volume_id)

        volumes.append(volume)

    return instance, volumes


def attach(project_id, volume_id, instance_id):
    """
    attach one or more 'available' volume_ids
    to 'running' or 'stopped' instance
    """

    # actually we just support only on volume action at a time.
    # but for exception & job consistency,
    # we use array for future process here.
    logger.info('.attach() begin, volume_id: %s, instance_id: %s' %
                (volume_id, instance_id))

    volume_ids = [volume_id]

    attachings = []
    exceptions = []

    with base.open_transaction(db.DB):
        instance, volumes = _pre_attach(project_id, volume_ids, instance_id)
        for volume in volumes:
            try:
                op_api.do_attach_volume(instance, volume)
            except Exception as ex:
                exceptions.append({
                    'resouece_id': volume['id'],
                    'exception': ex
                })
                continue

            attachings.append(volume['id'])
            Volume.update(volume['id'], **{
                'status': VOLUME_STATUS_ATTACHING,
                'updated': datetime.datetime.utcnow(),
            })
            instance_volume_model.create(volume['id'],
                                         instance['id'])

    logger.info('.attach() OK, attachings: %s, exceptions: %s' %
                (len(attachings), len(exceptions)))

    return model.actions_job('AttachVolumes',
                             project_id,
                             attachings,
                             exceptions)


def _pre_detach(project_id, volume_ids, instance_id):
    """
    check pre-conditions before detaching.

    instance should be 'active' or 'stopped'; volumes should be 'in-use'
    if status are inappropriate, raise exception
    else return instance and volumes models.
    """
    with base.lock_for_update():
        instance = instance_model.get(instance_id)

    instance.must_belongs_project(project_id)

    if not instance.status_detachable():
        raise iaas_error.InstanceCanNotBeDetached(instance_id)

    volumes = []
    for volume_id in volume_ids:
        with base.lock_for_update():
            volume = get(volume_id)

        volume.must_belongs_project(project_id)

        if not volume.status_detachable():
            raise iaas_error.VolumeCanNotDetach(volume_id)

        try:
            instance_volume_model.get(volume_id, instance_id)
        except:
            # the volume is not attached to the instance before!
            raise iaas_error.DetachVolumeWhenNotAttached(volume_id, instance_id)  # noqa

        volumes.append(volume)

    return instance, volumes


def detach(project_id, volume_ids, instance_id):
    """
    detach a 'in-use' volume from an instance
    """
    logger.info('.detach() begin, total count: %s, volume_ids: %s' %
                (len(volume_ids), volume_ids))
    exceptions = []
    detachings = []

    with base.open_transaction(db.DB):
        instance, volumes = _pre_detach(project_id, volume_ids, instance_id)
        for volume in volumes:
            try:
                op_api.do_detach_volume(instance, volume)
            except Exception as ex:
                exceptions.append({
                    'resouece_id': volume['id'],
                    'exception': ex
                })
                continue

            detachings.append(volume['id'])
            Volume.update(volume['id'], **{
                'status': VOLUME_STATUS_DETACHING,
                'updated': datetime.datetime.utcnow(),
            })
            instance_volume_model.delete(volume['id'], instance['id'])

    logger.info('.detach() OK, detachings: %s, exceptions: %s' %
                (len(detachings), len(exceptions)))

    return model.actions_job('DetachVolumes',
                             project_id,
                             detachings,
                             exceptions)


def _pre_extend(project, volume_ids, new_size):
    """
    check pre-conditions before extending.

    Preconditions
        Volume status must be available.
        Sufficient amount of block must exist to extend the volume.
        The user quota must have sufficient volume block.

    if status are inappropriate, raise exception
    else return volumes models.
    """
    delta_volume_size = 0
    volumes = []
    for volume_id in volume_ids:
        with base.lock_for_update():
            volume = get(volume_id)

        volume.must_belongs_project(project['id'])

        if not volume.status_extendable():
            raise iaas_error.VolumeCanNotExtend(volume_id)
        if volume['size'] >= new_size:
            raise iaas_error.VolumeNewSizeTooSmall()

        delta_volume_size += new_size - volume['size']
        volumes.append(volume)

    project.must_have_enough_quotas(volume_size=delta_volume_size)

    return volumes, delta_volume_size


def extend(project_id, volume_ids, new_size):
    logger.info('.extend() begin, total count: %s, volume_ids: %s' %
                (len(volume_ids), volume_ids))

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        volumes, delta_volume_size = _pre_extend(project, volume_ids, new_size)

        # assume extend success
        project.consume_quotas(volume_size=delta_volume_size)

    qt_volume_size = 0
    extendings = []
    exceptions = []

    with base.open_transaction(db.DB):
        volumes, _ = _pre_extend(project, volume_ids, new_size)
        for volume in volumes:
            volume_id = volume['id']
            try:
                op_api.do_extend_volume(volume, new_size)
            except Exception as ex:
                exceptions.append({
                    'resouece_id': volume_id,
                    'exception': ex
                })
                continue

            extendings.append(volume_id)
            qt_volume_size += new_size - volume['size']
            Volume.update(volume_id, **{
                'size': new_size,
                'status': VOLUME_STATUS_PENDING,
                'updated': datetime.datetime.utcnow(),
            })

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)
        # but we actually consume qt_volume_size, release those left.
        project.release_quotas(volume_size=delta_volume_size - qt_volume_size)

    logger.info('.extend() OK, extendings: %s, exceptions: %s' %
                (len(extendings), len(exceptions)))

    return model.actions_job('ExtendVolumes',
                             project_id,
                             extendings,
                             exceptions)


def modify(project_id, volume_id, name=None, description=None):
    logger.info('.modify() begin, volume_id: %s' % volume_id)

    volume = get(volume_id)
    volume.must_belongs_project(project_id)

    if name is None:
        name = volume['name']

    if description is None:
        description = volume['description']

    Volume.update(volume_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')

    volume = get(volume_id)
    return volume


def sync(volume_id):
    logger.info('.sync() begin, volume_id: %s' % volume_id)
    volume = get(volume_id)

    try:
        provider_volume = op_api.do_get_volume(volume['op_volume_id'])
    except:
        Volume.update(volume_id, **{
            'status': VOLUME_STATUS_ERROR,
            'updated': datetime.datetime.utcnow(),
        })
        raise

    provider_status = provider_volume['status']
    logger.info('provider volume status (%s).' % provider_status)

    status = VOLUME_STATE_MAP[provider_status]

    logger.info('volume (%s) status: (%s) => (%s) .' %
                (volume['id'], volume['status'], status))  # noqa

    Volume.update(volume_id, **{
        'status': status,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.sync() OK')
    volume = get(volume_id)
    return volume


def get(volume_id):
    logger.info('.get() begin, volume_id: %s' % volume_id)
    volume = Volume.get_as_model(volume_id)
    if volume is None:
        raise iaas_error.VolumeNotFound(volume_id)

    instance_rels = instance_volume_model.relations_from_volumes([volume_id])
    instance_id = instance_rels[volume_id]
    volume['instance_id'] = instance_id

    logger.info('.get() OK')
    return volume


def limitation(project_ids=None, status=None, volume_ids=None, verbose=False,
               search_word=None, offset=0, limit=10, reverse=True):
    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, volume_ids)
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filters.filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() begin')
    page = Volume.limitation_as_model(where,
                                      offset=offset,
                                      limit=limit,
                                      order_by=filters.order_by(reverse))

    volume_ids = [volume['id'] for volume in page['items']]
    instance_rels = instance_volume_model.relations_from_volumes(volume_ids)

    from icebox.model.iaas import instance as instance_model

    for volume in page['items']:
        instance_id = instance_rels[volume['id']]
        volume['instance_id'] = instance_id

        if verbose:
            logger.debug('require verbose result')
            if instance_id:
                volume['instance'] = instance_model.get(instance_id)
            else:
                volume['instance'] = None

    logger.info('.limitation() OK')

    return page


def erase(volume_id):
    logger.info('.erase() begin, volume_id: %s' % volume_id)
    volume = get(volume_id)

    if volume['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if volume['status'] == VOLUME_STATUS_DELETED:
        op_api.do_delete_volume(volume=volume)

        Volume.update(volume_id, **{
            'status': VOLUME_STATUS_CEASED,
            'ceased': datetime.datetime.utcnow(),
        })
        logger.info('.erase() OK.')

    else:
        logger.warn('volume status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
