from icebox import model
import time
import datetime
import traceback
from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from densefog.model.job import job as job_model

from icebox.model.project import project as project_model
from icebox.model.iaas import waiter
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import floatingip as floatingip_model

from icebox.model.iaas.openstack import network as network_provider
from icebox.model.iaas.openstack import api as op_api

from densefog import logger
logger = logger.getChild(__file__)

DEFAULT_BANDWIDTH = 1

WAIT_PORT_DELETE_TIMEOUT = 60

NETWORK_STATUS_PENDING = 'pending'
NETWORK_STATUS_ACTIVE = 'active'
NETWORK_STATUS_BUILDING = 'building'
NETWORK_STATUS_DISABLED = 'disabled'
NETWORK_STATUS_ERROR = 'error'
NETWORK_STATUS_DELETED = 'deleted'


NETWORK_STATUS_MAP = {
    (network_provider.NET_STATUS_ACTIVE, network_provider.ROUTER_STATUS_ACTIVE): NETWORK_STATUS_ACTIVE,  # noqa
    (network_provider.NET_STATUS_BUILD, network_provider.ROUTER_STATUS_ACTIVE): NETWORK_STATUS_PENDING,  # noqa
    (network_provider.NET_STATUS_DOWN, network_provider.ROUTER_STATUS_ACTIVE): NETWORK_STATUS_DISABLED,  # noqa
    (network_provider.NET_STATUS_ERROR, network_provider.ROUTER_STATUS_ACTIVE): NETWORK_STATUS_ERROR,  # noqa
    (network_provider.NET_STATUS_ACTIVE, network_provider.ROUTER_STATUS_ALLOCATING): NETWORK_STATUS_BUILDING,  # noqa
    (network_provider.NET_STATUS_BUILD, network_provider.ROUTER_STATUS_ALLOCATING): NETWORK_STATUS_BUILDING,  # noqa
    (network_provider.NET_STATUS_DOWN, network_provider.ROUTER_STATUS_ALLOCATING): NETWORK_STATUS_DISABLED,  # noqa
    (network_provider.NET_STATUS_ERROR, network_provider.ROUTER_STATUS_ALLOCATING): NETWORK_STATUS_ERROR,  # noqa
}


class Network(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.network

    def status_deletable(self):
        return self['status'] in [
            NETWORK_STATUS_ACTIVE,
            NETWORK_STATUS_ERROR
        ]

    def format(self):
        formated = {
            'networkId': self['id'],
            'projectId': self['project_id'],
            'name': self['name'],
            'description': self['description'],
            'externalGatewayIp': self['external_gateway_ip'],
            'externalGatewayBandwidth': self['external_gateway_bandwidth'],
            'status': self['status'],
            'updated': self['updated'],
            'created': self['created'],
            'deleted': self['deleted'],
        }
        return formated


def create(project_id, name='', description=''):
    logger.info('.create() begin')

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        # assume creation success
        project.must_have_enough_quota('networks', 1)
        project.consume_quota('networks', 1)

    op_project_id = project['op_project_id']

    key = utils.generate_key(8)
    network_id = 'net-%s' % key
    router_id = 'rutr-%s' % key

    try:
        # use icebox model id as openstack resource name
        op_router = op_api.do_create_router(op_project_id, name=router_id)
        op_network = op_api.do_create_network(op_project_id, name=network_id)

    except Exception:
        # after silently clean up, re-raise current exception
        with utils.defer_reraise():

            # delete router and network.
            with utils.silent():
                op_api.do_delete_router(op_router['id'])
            with utils.silent():
                op_api.do_delete_network(op_network['id'])

            # rollback the quota
            with base.open_transaction(db.DB):
                with base.lock_for_update():
                    project = project_model.get(project_id)
                project.release_quota('networks', 1)

    network_id = Network.insert(**{
        'id': network_id,
        'project_id': project_id,
        'name': name,
        'description': description,
        'external_gateway_ip': '',
        'external_gateway_bandwidth': 0,
        'status': NETWORK_STATUS_PENDING,
        'op_router_id': op_router['id'],
        'op_network_id': op_network['id'],
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })

    logger.info('.create() OK.')

    return model.actions_job('CreateNetworks',
                             project_id,
                             [network_id],
                             [])


def modify(project_id, network_id, name=None, description=None):
    logger.info('.modify() begin, network_id: %s' % network_id)

    network = get(network_id)
    network.must_belongs_project(project_id)

    if name is None:
        name = network['name']

    if description is None:
        description = network['description']

    Network.update(network_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')

    network = get(network_id)
    return network


def _pre_set_external_gateway(project_id, network_ids):
    networks = []
    for network_id in network_ids:
        with base.lock_for_update():
            network = get(network_id)

        network.must_belongs_project(project_id)
        networks.append(network)

    return networks


@base.transaction
def set_external_gateway(project_id, network_ids, bandwidth=DEFAULT_BANDWIDTH):
    logger.info('.set_external_gateway() begin, network_ids: %s' % network_ids)

    networks = _pre_set_external_gateway(project_id, network_ids)

    seteds = []
    exceptions = []
    for network in networks:
        op_router_id = network['op_router_id']

        try:
            op_router = op_api.do_set_gateway_router(op_router_id, rate_limit=bandwidth)   # noqa
            external_fixed_ips = op_router['external_gateway_info']['external_fixed_ips']  # noqa
            external_gateway_ip = external_fixed_ips[0]['ip_address']

        except Exception as e:
            exceptions.append({
                'network_id': network['id'],
                'exception': e
            })

        else:
            Network.update(network['id'],
                           external_gateway_ip=external_gateway_ip,
                           external_gateway_bandwidth=bandwidth)

            # this floating ip is used by router.
            floatingip_model.consume_ips([external_gateway_ip])
            seteds.append(network['id'])

    logger.info('.set_external_gateway() OK.')
    return model.actions_result(seteds,
                                exceptions)


def _pre_unset_external_gateway(project_id, network_ids):
    from icebox.model.iaas import instance as instance_model
    from icebox.model.iaas import eip_resource as eip_resource_model

    # network's instances should not bind to any eip.
    instances = instance_model.limitation(network_ids=network_ids, limit=0)['items']  # noqa
    instance_ids = [instance['id'] for instance in instances]
    eip_rels = eip_resource_model.relations_from_instances(instance_ids)
    bindings = []
    for instance_id, eip_id in eip_rels.items():
        if eip_id:
            bindings.append(instance_id)
    if bindings:
        raise iaas_error.RemoveExternalGatewayWhenInstancesBindingEip(bindings)  # noqa

    networks = []
    for network_id in network_ids:
        with base.lock_for_update():
            network = get(network_id)

        network.must_belongs_project(project_id)
        networks.append(network)

    return networks


@base.transaction
def unset_external_gateway(project_id, network_ids):
    logger.info('.unset_external_gateway() begin, '
                'total count: %s, network_ids: %s' %
                (len(network_ids), network_ids))

    networks = _pre_unset_external_gateway(project_id, network_ids)

    removeds = []
    exceptions = []
    for network in networks:
        op_router_id = network['op_router_id']

        try:
            op_api.do_remove_gateway_router(op_router_id)
        except Exception as e:
            exceptions.append({
                'network_id': network['id'],
                'exception': e
            })

        else:
            Network.update(network['id'],
                           external_gateway_ip='',
                           external_gateway_bandwidth=0)
            # this ip is unset from router
            floatingip_model.release_ips([network['external_gateway_ip']])
            removeds.append(network['id'])

    logger.info('.unset_external_gateway() OK.')
    return model.actions_result(removeds,
                                exceptions)


def _pre_delete(project, network_ids):
    networks = []
    for network_id in network_ids:
        with base.lock_for_update():
            network = get(network_id)

        network.must_belongs_project(project['id'])
        if not network.status_deletable():
            raise iaas_error.NetworkCanNotDelete(network_id)

        # there must not be any instances in the network.
        if count_instances(network_id) > 0:
            raise iaas_error.DeleteNetworkWhenInstancesInSubnet(network_id)

        # there must not be any loadbalancers in the network.
        if count_load_balancers(network_id) > 0:
            raise iaas_error.DeleteNetworkWhenResourcesInSubnet(network_id)

        # the network must not have external gateway.
        if network['external_gateway_ip']:
            raise iaas_error.DeleteNetworkWhenHasExternalGateway(network_id)

        networks.append(network)

    return networks


@base.transaction
def delete(project_id, network_ids):
    logger.info('.delete() begin. '
                'total count: %s, network_ids: %s' %
                (len(network_ids), network_ids))

    with base.lock_for_update():
        project = project_model.get(project_id)

    networks = _pre_delete(project, network_ids)

    for network in networks:
        Network.update(network['id'], **{
            'status': NETWORK_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    project.release_quota('networks', len(network_ids))

    logger.info('.delete() OK.')

    job_model.create(
        action='EraseNetworks',
        params={
            'resource_ids': network_ids
        },
        run_at=utils.seconds_later(10),   # as fast as possible
        try_period=10)


def get(network_id):
    logger.info('.get() begin. network_id: %s' % network_id)

    network = Network.get_as_model(network_id)
    if network is None:
        raise iaas_error.NetworkNotFound(network_id)
    logger.info('.get() OK.')
    return network


def count_instances(network_id):
    """
    count instances in the network.
    setp 1. filter out deleted subnets.
    step 2. filter out deleted and ceased instances.
    step 3. count them.
    """
    from icebox.model.iaas import subnet as subnet_model

    page = subnet_model.limitation(network_ids=[network_id], limit=0,
                                   status=subnet_model.SUBNET_STATUS_ACTIVE)
    count = 0
    for subnet in page['items']:
        count += subnet_model.count_instances(subnet['id'])

    return count


def count_load_balancers(network_id):
    """
    count instances in the network.
    setp 1. filter out deleted subnets.
    step 2. filter out deleted loadbalancers.
    step 3. count them.
    """
    from icebox.model.iaas import subnet as subnet_model

    page = subnet_model.limitation(network_ids=[network_id], limit=0,
                                   status=subnet_model.SUBNET_STATUS_ACTIVE)
    count = 0
    for subnet in page['items']:
        count += subnet_model.count_resources(
            subnet['id'], subnet_model.RESOURCE_TYPE_LOAD_BALANCER)

    return count


def limitation(network_ids=None, status=None, project_ids=None, verbose=False,
               search_word=None, offset=0, limit=10, reverse=True):
    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, network_ids)
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filters.filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() begin.')

    page = Network.limitation_as_model(where,
                                       limit=limit,
                                       offset=offset,
                                       order_by=filters.order_by(reverse))
    if verbose:
        logger.info('require verbose result.')
        from icebox.model.iaas import subnet as subnet_model

        network_map = {}
        for network in page['items']:
            network['subnets'] = []
            network_map[network['id']] = network

        subnets = subnet_model.limitation(network_ids=network_map.keys(),
                                          limit=0)
        for subnet in subnets['items']:
            # filter out deleted subnets
            if subnet['status'] == subnet_model.SUBNET_STATUS_DELETED:
                continue
            network = network_map[subnet['network_id']]
            network['subnets'].append(subnet)

    logger.info('.limitation() OK.')

    return page


def sync(network_id):
    logger.info('.sync() begin. network_id: %s' % network_id)
    network = get(network_id)

    op_network_id = network['op_network_id']
    op_router_id = network['op_router_id']

    try:
        op_network = op_api.do_get_network(op_network_id)
        op_router = op_api.do_get_router(op_router_id)
    except:
        Network.update(network_id, **{
            'status': NETWORK_STATUS_ERROR,
            'updated': datetime.datetime.utcnow(),
        })
        raise

    op_network_status = op_network['status']
    op_router_status = op_router['status']

    logger.info('provider network status (%s), router status (%s).' %
                (op_network_status, op_router_status))

    status = NETWORK_STATUS_MAP[(op_network_status, op_router_status)]

    logger.info('network (%s) status: (%s) => (%s) .' %
                (network['id'], network['status'], status))  # noqa

    Network.update(network_id, **{
        'status': status,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.sync() OK.')

    network = get(network_id)
    return network


def erase(network_id):
    """
    step 0: delete any ports from the network.
    step 1: detach subnet from router
    step 2: delete subnet
    step 3: delete port_forwarding
    step 4: delete router
    step 5: delete network.
    """
    from icebox.model.iaas import subnet as subnet_model
    from icebox.model.iaas import port_forwarding as pf_model

    logger.info('.erase() begin. network_id: %s' % network_id)
    network = get(network_id)

    if network['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if network['status'] == NETWORK_STATUS_DELETED:
        # delete any ports from the network.
        # maybe forget when delete instance.
        try:
            op_ports = op_api.do_list_ports(op_network_id=network['op_network_id'])  # noqa
            for op_port in op_ports:
                op_api.do_delete_port(op_port['id'])
                waiter.wait_port_deleted(op_port['id'],
                                         timeout=WAIT_PORT_DELETE_TIMEOUT)
        except Exception as ex:
            trace = traceback.format_exc()
            raise iaas_error.ProviderDeletePortError(ex, trace)

        subnets = subnet_model.limitation(
            network_ids=[network_id], limit=0,
            status=subnet_model.SUBNET_STATUS_ACTIVE)['items']

        # TODO. NEED WAIT PORT DELETED FINISH!

        # detach subnet
        # delete subnet
        for subnet in subnets:
            op_subnet_id = subnet['op_subnet_id']
            op_router_id = subnet['op_router_id']

            op_api.do_detach_subnet(op_subnet_id, op_router_id)
            op_api.do_delete_subnet(op_subnet_id)

            subnet_model.Subnet.update(subnet['id'], **{
                'status': subnet_model.SUBNET_STATUS_DELETED,
                'deleted': datetime.datetime.utcnow(),
            })

        # delete port forwarding
        port_forwardings = pf_model.limitation(
            network_ids=[network_id], limit=0,
            status=pf_model.PORT_FORWARDING_STATUS_ACTIVE)['items']

        for pf in port_forwardings:
            op_api.do_remove_port_forwarding(pf['op_router_id'],
                                             pf['op_port_forwarding_id'])

            pf_model.PortForwarding.update(pf['id'], **{
                'status': pf_model.PORT_FORWARDING_STATUS_DELETED,
                'deleted': datetime.datetime.utcnow(),
            })

        # delete router
        # for some reason, delete router here may raise 'still has ports'
        # and some seconds later, delete router will succeed
        # (as report by worker logs).
        # so we retry 3 times, every time sleep 5 seconds.
        with utils.retry_on_exc(times=3, step=5, sleep=time.sleep):
            op_api.do_delete_router(network['op_router_id'])

        # delete network
        with utils.retry_on_exc(times=3, step=5, sleep=time.sleep):
            op_api.do_delete_network(network['op_network_id'])

        Network.update(network_id, **{
            'ceased': datetime.datetime.utcnow(),
        })
        logger.info('.erase() OK. ceased.')

    else:
        logger.warn('network status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
