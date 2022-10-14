import datetime
from netaddr import IPAddress
from sqlalchemy.sql import and_, not_

from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from densefog.model.job import job as job_model

from icebox.model.project import project as project_model
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import network as network_model
from icebox.model.iaas.openstack import api as op_api

from densefog import logger
logger = logger.getChild(__file__)

SUBNET_STATUS_ACTIVE = 'active'
SUBNET_STATUS_DELETED = 'deleted'

RESOURCE_TYPE_LOAD_BALANCER = 'loadBalancer'
RESOURCE_TYPE_SERVER = 'server'


class Subnet(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.subnet

    def status_deletable(self):
        return self['status'] in [
            SUBNET_STATUS_ACTIVE
        ]

    def contain_address(self, ip):
        # return if the ip is in subnet. no exceptions, just true/false.
        try:
            addr = IPAddress(ip)
            start = IPAddress(self['ip_start'])
            end = IPAddress(self['ip_end'])
            return start <= addr <= end

        except:
            return False

    def format(self):
        formated = {
            'subnetId': self['id'],
            'projectId': self['project_id'],
            'networkId': self['network_id'],
            'name': self['name'],
            'description': self['description'],
            'gatewayIp': self['gateway_ip'],
            'ipStart': self['ip_start'],
            'ipEnd': self['ip_end'],
            'cidr': self['cidr'],
            'status': self['status'],
            'updated': self['updated'],
            'created': self['created'],
            'deleted': self['deleted'],
        }
        return formated


@base.transaction
def create(project_id, network_id, name='', description='',
           cidr='192.168.100.0/24'):
    logger.info('.create() begin')

    # do not need to lock project. no quota related.
    project = project_model.get(project_id)

    with base.lock_for_update():
        network = network_model.get(network_id)

    network.must_belongs_project(project_id)
    network.must_not_deleted()
    network.must_not_error()

    op_project_id = project['op_project_id']
    op_network_id = network['op_network_id']
    op_router_id = network['op_router_id']

    subnet_id = 'snt-%s' % utils.generate_key(8)

    try:
        # use icebox model id as openstack resource name
        subnet = op_api.do_create_subnet(op_project_id,
                                         op_network_id,
                                         name=subnet_id,
                                         cidr=cidr)
    except Exception as ex:
        if hasattr(ex, 'is_dup_subnet') and ex.is_dup_subnet():
            raise iaas_error.SubnetCreateDuplicatedCIDRError(cidr)
        if hasattr(ex, 'is_invalid_cidr') and ex.is_invalid_cidr():
            raise iaas_error.SubnetCreateInvalidCIDRError(cidr)

        raise

    op_api.do_attach_subnet(subnet['id'], op_router_id)

    subnet_id = Subnet.insert(**{
        'id': subnet_id,
        'project_id': project_id,
        'network_id': network_id,
        'op_subnet_id': subnet['id'],
        'op_network_id': op_network_id,
        'op_router_id': op_router_id,
        'name': name,
        'description': description,
        'gateway_ip': subnet['gateway_ip'],
        'ip_start': subnet['allocation_pools'][0]['start'],
        'ip_end': subnet['allocation_pools'][0]['end'],
        'cidr': cidr,
        'status': SUBNET_STATUS_ACTIVE,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    logger.info('.create() OK.')
    return subnet_id


def _pre_delete(project_id, subnet_ids):
    subnets = []
    for subnet_id in subnet_ids:
        with base.lock_for_update():
            subnet = get(subnet_id)
            network = network_model.get(subnet['network_id'])

        subnet.must_belongs_project(project_id)
        network.must_be_available()

        if not subnet.status_deletable():
            raise iaas_error.SubnetCanNotDelete(subnet_id)

        if count_instances(subnet_id) > 0:
            raise iaas_error.DeleteSubnetWhenInstancesInSubnet(subnet_id)

        if count_resources(subnet_id) > 0:
            raise iaas_error.DeleteSubnetWhenResourcesInSubnet(subnet_id)

        subnets.append(subnet)

    return subnets


@base.transaction
def delete(project_id, subnet_ids):
    logger.info('.delete() begin, '
                'total count: %s, subnet_ids: %s' %
                (len(subnet_ids), subnet_ids))
    subnets = _pre_delete(project_id, subnet_ids)

    for subnet in subnets:
        Subnet.update(subnet['id'], **{
            'status': SUBNET_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    logger.info('.delete() OK.')
    job_model.create(
        action='EraseSubnets',
        params={
            'resource_ids': subnet_ids
        },
        run_at=utils.seconds_later(10),   # as fast as possible
        try_period=10)


def get(subnet_id):
    logger.info('.get() begin, subnet_id: %s' % subnet_id)

    subnet = Subnet.get_as_model(subnet_id)
    if subnet is None:
        raise iaas_error.SubnetNotFound(subnet_id)
    logger.info('.get() OK.')
    return subnet


def count_instances(subnet_id):
    """
    count instance in the subnet. filter out deleted and ceased instances.
    """
    from icebox.model.iaas import instance as instance_model

    def where(t):
        _where = True
        _where = and_(_where, t.subnet_id == subnet_id)
        _where = and_(_where,
                      not_(t.status.in_([
                          instance_model.INSTANCE_STATUS_DELETED,
                          instance_model.INSTANCE_STATUS_CEASED])
                      ))

        return _where

    count = instance_model.Instance.count(where)
    return count


def count_resources(subnet_id, resource_type=None):
    """
    count resources in the subnet.
    if given the resource_type, count for this type.
    otherwise count for every resource_types.
    """
    from icebox.model.iaas import subnet_resource as subres_model

    if resource_type is None:
        count = subres_model.count(subnet_id, resource_type)
    else:
        c1 = subres_model.count(subnet_id, RESOURCE_TYPE_LOAD_BALANCER)
        c2 = subres_model.count(subnet_id, RESOURCE_TYPE_SERVER)
        count = c1 + c2

    return count


def limitation(subnet_ids=None, status=None,
               project_ids=None, network_ids=None,
               search_word=None, offset=0, limit=10, reverse=True):

    """
    can search by id, cidr
    """
    from sqlalchemy.sql import and_, or_

    def filter_search_word(where, t, search_word):
        if search_word is None:
            pass
        else:
            where = and_(where,
                         or_(
                             t.cidr.like('%' + search_word + '%'),
                             t.id.like('%' + search_word + '%'),
                         ))
        return where

    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, subnet_ids)
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)

        if network_ids is None:
            pass
        elif len(network_ids) == 0:
            _where = False
        else:
            _where = Subnet.and_(t.network_id.in_(network_ids), _where)

        return _where

    logger.info('.limitation() begin.')
    page = Subnet.limitation_as_model(where,
                                      limit=limit,
                                      offset=offset,
                                      order_by=filters.order_by(reverse))
    logger.info('.limitation() OK.')
    return page


def modify(project_id, subnet_id, name=None, description=None):
    logger.info('.modify() begin. subnet_id: %s' % subnet_id)
    subnet = get(subnet_id)
    subnet.must_belongs_project(project_id)

    if name is None:
        name = subnet['name']

    if description is None:
        description = subnet['description']

    Subnet.update(subnet_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')
    subnet = get(subnet_id)
    return subnet


def erase(subnet_id):
    logger.info('.erase() begin. subnet_id: %s' % subnet_id)
    subnet = get(subnet_id)

    if subnet['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if subnet['status'] == SUBNET_STATUS_DELETED:
        op_api.do_detach_subnet(subnet['op_subnet_id'], subnet['op_router_id'])
        op_api.do_delete_subnet(subnet['op_subnet_id'])

        Subnet.update(subnet_id, **{
            'ceased': datetime.datetime.utcnow(),
        })
        logger.info('.erase() OK.')

    else:
        logger.warn('subnet status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
