import datetime
from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas.openstack import compute as compute_provider
from icebox.model.iaas.openstack import api as op_api

from densefog import logger
logger = logger.getChild(__file__)

HYPERVISOR_STATUS_ENABLED = 'enabled'
HYPERVISOR_STATUS_DISABLED = 'disabled'
HYPERVISOR_STATUS_MAP = {
    compute_provider.HYPERVISOR_STATUS_ENABLED: HYPERVISOR_STATUS_ENABLED,
    compute_provider.HYPERVISOR_STATUS_DISABLED: HYPERVISOR_STATUS_DISABLED,
}

HYPERVISOR_STATE_UP = 'up'
HYPERVISOR_STATE_DOWN = 'down'
HYPERVISOR_STATE_MAP = {
    compute_provider.HYPERVISOR_STATE_UP: HYPERVISOR_STATE_UP,
    compute_provider.HYPERVISOR_STATE_DOWN: HYPERVISOR_STATE_DOWN,
}


class Hypervisor(base.StatusModel):

    @classmethod
    def db(cls):
        return db.DB.hypervisor

    def format(self):
        formated = {
            'hypervisorId': self['id'],
            'name': self['name'],
            'description': self['description'],
            'state': self['state'],
            'status': self['status'],
            'updated': self['updated'],
            'created': self['created'],
        }
        return formated


def limitation(ids=None, status=None, states=None, names=None,
               search_word=None, offset=0, limit=10, reverse=True):
    """
    if is_public, return paged public hypervisors.
    if is not public, then return project_ids's private hypervisors.
    if neither public nor project_ids is passed in,
        then return paged hypervisors with a few filters,
        like search_word, status, etc..
    """
    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, ids)
        _where = filters.filter_status(_where, t, status)
        _where = filters.filter_states(_where, t, states)
        _where = filters.filter_names(_where, t, names)
        _where = filters.filter_search_word(_where, t, search_word)
        return _where

    logger.info('.limitation() start')
    page = Hypervisor.limitation_as_model(where,
                                          limit=limit,
                                          offset=offset,
                                          order_by=filters.order_by(reverse))

    logger.info('.limitation() OK. get hypervisors: %s' % len(page['items']))

    return page


def sync_all():
    logger.info('.sync_all() start')

    hypervisors = op_api.do_list_hypervisors()

    for hypervisor in hypervisors:
        hypervisor_status = HYPERVISOR_STATUS_MAP[hypervisor['status']]
        hypervisor_state = HYPERVISOR_STATE_MAP[hypervisor['state']]
        hypervisor_db = Hypervisor.first(
            lambda t: t['op_hyper_id'] == hypervisor['id'])

        if hypervisor_db:
            logger.info('hypervisor exists in db hypervisor, update.')
            Hypervisor.update(hypervisor['id'], **{
                'current_workload': hypervisor['current_workload'],
                'disk_available_least': hypervisor['disk_available_least'],
                'free_disk_gb': hypervisor['free_disk_gb'],
                'free_ram_mb': hypervisor['free_ram_mb'],
                'local_gb_used': hypervisor['local_gb_used'],
                'memory_mb_used': hypervisor['memory_mb_used'],
                'running_vms': hypervisor['running_vms'],
                'state': hypervisor_state,
                'status': hypervisor_status,
                'vcpus_used': hypervisor['vcpus_used'],
                'updated': datetime.datetime.utcnow(),
            })
        else:
            logger.info('hypervisor not exists in db hypervisor, insert.')
            Hypervisor.insert(**{
                'id': 'hyper-%s' % utils.generate_key(8),
                'op_hyper_id': hypervisor['id'],
                'name': hypervisor['hypervisor_hostname'],
                'current_workload': hypervisor['current_workload'],
                'disk_available_least': hypervisor['disk_available_least'],
                'free_disk_gb': hypervisor['free_disk_gb'],
                'free_ram_mb': hypervisor['free_ram_mb'],
                'host_ip': hypervisor['host_ip'],
                'hypervisor_type': hypervisor['hypervisor_type'],
                'hypervisor_version': hypervisor['hypervisor_version'],
                'local_gb': hypervisor['local_gb'],
                'local_gb_used': hypervisor['local_gb_used'],
                'memory_mb': hypervisor['memory_mb'],
                'memory_mb_used': hypervisor['memory_mb_used'],
                'running_vms': hypervisor['running_vms'],
                'state': hypervisor_state,
                'status': hypervisor_status,
                'vcpus': hypervisor['vcpus'],
                'vcpus_used': hypervisor['vcpus_used'],
                'description': '',
                'updated': datetime.datetime.utcnow(),
                'created': datetime.datetime.utcnow(),
            })

        logger.info('.sync_all() OK.')


def get(hypervisor_id):
    logger.info('.get() start. hypervisor: %s' % hypervisor_id)
    hypervisor = Hypervisor.get_as_model(hypervisor_id)
    if hypervisor is None:
        raise iaas_error.HypervisorNotFound(hypervisor_id)
    logger.info('.get() OK.')
    return hypervisor


def modify(hypervisor_id, name=None, description=None):
    """
    modify hypervisors. name & description
    """
    logger.info('.modify() start')
    hypervisor = get(hypervisor_id)

    if name is None:
        name = hypervisor['name']
    if description is None:
        description = hypervisor['description']

    Hypervisor.update(hypervisor_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')
