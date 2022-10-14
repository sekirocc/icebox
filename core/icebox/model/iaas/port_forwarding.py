import datetime

from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters

from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import network as network_model
from icebox.model.iaas import subnet as subnet_model
from icebox.model.iaas.openstack import api as op_api
from densefog.model.job import job as job_model

from densefog import logger
logger = logger.getChild(__file__)

PORT_FORWARDING_STATUS_ACTIVE = 'active'
PORT_FORWARDING_STATUS_DELETED = 'deleted'


class PortForwarding(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.port_forwarding

    def status_deletable(self):
        return self['status'] in [
            PORT_FORWARDING_STATUS_ACTIVE,
        ]

    def format(self):
        formated = {
            'portForwardingId': self['id'],
            'projectId': self['project_id'],
            'networkId': self['network_id'],
            'protocol': self['protocol'],
            'outsidePort': self['outside_port'],
            'insideAddress': self['inside_address'],
            'insidePort': self['inside_port'],
            'status': self['status'],
            'name': self['name'],
            'description': self['description'],
            'updated': self['updated'],
            'deleted': self['deleted'],
            'created': self['created'],
        }
        return formated


def _pre_create(project_id, network_id, outside_port, inside_address):
    with base.lock_for_update():
        network = network_model.get(network_id)

    network.must_belongs_project(project_id)
    network.must_be_available()

    found = False

    # inside_address should be in one of the subnets.
    subnets = subnet_model.limitation(
        network_ids=[network_id],
        status=subnet_model.SUBNET_STATUS_ACTIVE,
        limit=0)['items']
    for subnet in subnets:
        if subnet.contain_address(inside_address):
            found = True
            break

    if not found:
        raise iaas_error.PortForwardingInsideAddressNotInSubnetsError(inside_address)   # noqa

    # outside_port should not been used in network
    pfs = limitation(network_ids=[network_id],
                     status=[PORT_FORWARDING_STATUS_ACTIVE])['items']
    for pf in pfs:
        if pf['outside_port'] == outside_port:
            raise iaas_error.PortForwardingOutsidePortUsedError(outside_port)

    return network


@base.transaction
def create(project_id, network_id, protocol, outside_port,
           inside_address, inside_port):
    logger.info('.create() begin')

    network = _pre_create(project_id, network_id, outside_port, inside_address)

    op_router_id = network['op_router_id']

    try:
        provider_pf = op_api.do_add_port_forwarding(op_router_id,
                                                    protocol,
                                                    outside_port,
                                                    inside_address,
                                                    inside_port)
    except Exception as ex:
        if hasattr(ex, 'not_match_subnets') and ex.not_match_subnets():
            raise iaas_error.PortForwardingInsideAddressNotInSubnetsError(inside_address)   # noqa
        if hasattr(ex, 'is_invalid_port') and ex.is_invalid_port():
            raise iaas_error.PortForwardingPortInvalid(outside_port, inside_port)  # noqa

        raise

    else:
        port_forwarding_id = PortForwarding.insert(**{
            'id': 'pf-%s' % utils.generate_key(8),
            'project_id': project_id,
            'network_id': network_id,
            'op_port_forwarding_id': provider_pf['id'],
            'op_router_id': provider_pf['router_id'],
            'protocol': protocol,
            'outside_port': outside_port,
            'inside_address': inside_address,
            'inside_port': inside_port,
            'name': '',
            'description': '',
            'status': PORT_FORWARDING_STATUS_ACTIVE,
            'deleted': None,
            'ceased': None,
            'updated': datetime.datetime.utcnow(),
            'created': datetime.datetime.utcnow(),
        })

        logger.info('.create() OK.')
        return port_forwarding_id


def _pre_delete(project_id, port_forwarding_ids):
    port_forwardings = []
    for pf_id in port_forwarding_ids:
        with base.lock_for_update():
            port_forwarding = get(pf_id)
            network = network_model.get(port_forwarding['network_id'])

        port_forwarding.must_belongs_project(project_id)
        network.must_be_available()

        if not port_forwarding.status_deletable():
            raise iaas_error.PortForwardingUnDeletableError(pf_id)

        port_forwardings.append(port_forwarding)

    return port_forwardings


@base.transaction
def delete(project_id, port_forwarding_ids):
    logger.info('.delete() begin, total count: %s, port_forwarding_ids: %s' %
                (len(port_forwarding_ids), port_forwarding_ids))

    port_forwardings = _pre_delete(project_id, port_forwarding_ids)

    for port_forwarding in port_forwardings:
        PortForwarding.update(port_forwarding['id'], **{
            'status': PORT_FORWARDING_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    logger.info('.delete() OK.')

    job_model.create(
        action='ErasePortForwardings',
        params={
            'resource_ids': port_forwarding_ids
        },
        run_at=utils.seconds_later(10),
        try_period=10)


def get(port_forwarding_id):
    logger.info('.get() begin, port_forwarding_id: %s' %
                port_forwarding_id)

    port_forwarding = PortForwarding.get_as_model(port_forwarding_id)
    if port_forwarding is None:
        raise iaas_error.PortForwardingNotFound(port_forwarding_id)

    logger.info('.get() OK.')
    return port_forwarding


def limitation(port_forwarding_ids=None, status=None, project_ids=None,
               network_ids=None, offset=0, limit=10,
               reverse=True, search_word=None):
    """
    can search by id, inside_address
    """
    from sqlalchemy.sql import and_, or_

    def filter_search_word(where, t, search_word):
        if search_word is None:
            pass
        else:
            where = and_(where,
                         or_(
                             t.inside_address.like('%' + search_word + '%'),
                             t.id.like('%' + search_word + '%'),
                         ))
        return where

    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, port_forwarding_ids)
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filters.filter_network_ids(_where, t, network_ids)
        _where = filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() begin.')
    page = PortForwarding.limitation_as_model(where,
                                              limit=limit,
                                              offset=offset,
                                              order_by=filters.order_by(reverse))  # noqa
    logger.info('.limitation() OK.')
    return page


def modify(project_id, port_forwarding_id, name=None, description=None):
    logger.info('.modify() begin. port_forwarding: %s' % port_forwarding_id)

    port_forwarding = get(port_forwarding_id)
    port_forwarding.must_belongs_project(project_id)

    if name is None:
        name = port_forwarding['name']

    if description is None:
        description = port_forwarding['description']

    PortForwarding.update(port_forwarding_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')

    port_forwarding = get(port_forwarding_id)
    return port_forwarding


def erase(port_forwarding_id):
    logger.info('.erase() begin. port_forwarding: %s' % port_forwarding_id)

    pf = get(port_forwarding_id)

    if pf['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if pf['status'] == PORT_FORWARDING_STATUS_DELETED:
        op_api.do_remove_port_forwarding(pf['op_router_id'],
                                         pf['op_port_forwarding_id'])

        PortForwarding.update(port_forwarding_id, **{
            'ceased': datetime.datetime.utcnow(),
        })
        logger.info('.erase() OK.')

    else:
        logger.warn('portforwarding status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
