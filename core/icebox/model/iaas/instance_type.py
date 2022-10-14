from icebox import model
import datetime

from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from densefog.model.job import job as job_model

from icebox import config
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas.openstack import api as op_api

from densefog import logger
logger = logger.getChild(__file__)

INSTANCE_TYPE_STATUS_ACTIVE = 'active'
INSTANCE_TYPE_STATUS_DELETED = 'deleted'

PUBLIC_INSTANCE_TYPE = utils.encode_uuid(
    '00000000-0000-0000-0000-000000000000')


class InstanceType(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.instance_type

    def format(self):
        formated = {
            'instanceTypeId': self['id'],
            'name': self['name'],
            'description': self['description'],
            'projectId': self['project_id'],
            'vcpus': self['vcpus'],
            'memory': self['memory'],
            'disk': self['disk'],
            'isPublic': self['project_id'] == PUBLIC_INSTANCE_TYPE,
            'status': self['status'],
            'updated': self['updated'],
            'created': self['created'],
            'deleted': self['deleted'],
        }
        if formated['isPublic']:
            formated['projectId'] = None
        return formated


def create(vcpus, memory, disk,
           description='',
           project_id=None):
    logger.info('.create() begin')

    name = 'c%sm%sd%s' % (vcpus, memory, disk)
    instance_type_id = 'itp-%s' % name

    if not op_api.do_find_flavor(instance_type_id):
        op_api.do_create_flavor(name=instance_type_id,
                                ram=memory,
                                vcpus=vcpus,
                                disk=disk,
                                flavorid=instance_type_id)
    op_api.do_update_flavor_quota(instance_type_id,
                                  disk_read_iops_sec=400,
                                  disk_write_iops_sec=400,
                                  disk_read_bytes_sec=50 * 1024 * 1024,
                                  disk_write_bytes_sec=50 * 1024 * 1024,
                                  vif_inbound_average=1000 * 1024 / 8,
                                  vif_outbound_average=1000 * 1024 / 8)

    exist_instance_type = InstanceType.get(instance_type_id)
    if exist_instance_type:
        InstanceType.update(exist_instance_type['id'], **{
            'status': INSTANCE_TYPE_STATUS_ACTIVE,
        })
        logger.debug('instance_type alreay exists. OK. active this one.')
    else:
        InstanceType.insert(**{
            'id': instance_type_id,
            'name': name,
            'description': description,
            'project_id': PUBLIC_INSTANCE_TYPE,
            'op_flavor_id': instance_type_id,
            'vcpus': vcpus,
            'memory': memory,
            'disk': disk,
            'status': INSTANCE_TYPE_STATUS_ACTIVE,
            'updated': datetime.datetime.utcnow(),
            'created': datetime.datetime.utcnow(),
        })
        logger.info('.create() OK.')
    return instance_type_id


def get(instance_type_id):
    logger.info('.get() begin, instance_type_id: %s' %
                instance_type_id)
    instance_type = InstanceType.get_as_model(instance_type_id)
    if instance_type is None:
        raise iaas_error.InstanceTypeNotFound(instance_type_id)

    logger.info('.get() OK.')
    return instance_type


def limitation(instance_type_ids=None, status=None, project_ids=None,
               is_public=True,
               search_word=None, offset=0, limit=10, reverse=True):
    def where(t):
        _where = True

        select_projects = [PUBLIC_INSTANCE_TYPE] if is_public else project_ids
        _where = filters.filter_project_ids(_where, t, select_projects)

        _where = filters.filter_ids(_where, t, instance_type_ids)
        _where = filters.filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() begin')

    page = InstanceType.limitation_as_model(where,
                                            limit=limit,
                                            offset=offset,
                                            order_by=filters.order_by(reverse))

    logger.info('.limitation() OK.')
    return page


def generate():
    logger.info('.generate() begin')
    generateds = []
    exceptions = []

    flavors = {
        1: [1, 2, 4, 8],
        2: [2, 4, 8, 16],
        4: [4, 8, 16, 32],
        8: [8, 16, 32, 64],
        16: [16, 32, 64],
    }
    disks = [40]

    for vcpus, rams in flavors.items():
        for ram in rams:
            if config.CONF.debug:
                ram = ram * 64
                disks = [2]
            else:
                ram = ram * 1024

            for disk in disks:
                try:
                    instance_type_id = create(vcpus=vcpus,
                                              memory=ram,
                                              disk=disk)
                except iaas_error.IaasProviderActionError as e:
                    exceptions.append({
                        'instance_type': None,
                        'exception': e
                    })
                else:
                    generateds.append(instance_type_id)

    logger.info('.generate() OK. generateds: %s, exceptions: %s' %
                (len(generateds), len(exceptions)))
    return model.actions_result(generateds,
                                exceptions)


def delete(project_id, instance_type_ids):
    logger.info('.delete() begin, total count: %s' %
                len(instance_type_ids))
    instance_types = []
    for instance_type_id in instance_type_ids:
        instance_type = get(instance_type_id)
        instance_type.must_belongs_project(project_id)
        instance_types.append(instance_type)

    for instance_type in instance_types:
        InstanceType.update(instance_type['id'], **{
            'status': INSTANCE_TYPE_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    logger.info('.delete() OK. deleteds: %s' %
                len(instance_type_ids))
    job_model.create(
        action='EraseInstanceTypes',
        params={
            'resource_ids': instance_type_ids
        },
        run_at=utils.seconds_later(10),   # as fast as possible
        try_period=10)


def erase(instance_type_id):
    logger.info('.erase() begin, instance_type_id: %s' %
                instance_type_id)

    instance_type = get(instance_type_id)

    if instance_type['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if instance_type['status'] == INSTANCE_TYPE_STATUS_DELETED:
        op_api.do_delete_flavor(instance_type['op_flavor_id'])

        InstanceType.update(instance_type_id, **{
            'ceased': datetime.datetime.utcnow(),
        })
        logger.info('.erase() OK.')

    else:
        logger.warn('instance_type status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
