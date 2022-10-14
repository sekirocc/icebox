import datetime
from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from icebox.model.iaas import error as iaas_error

from densefog import logger
logger = logger.getChild(__file__)


class SubnetResource(base.BaseModel):

    @classmethod
    def db(cls):
        return db.DB.subnet_resource


def add(subnet_id, resource_ids, resource_type):
    logger.info('.add() begin')
    logger.info('.add() begin, subnet_id: %s, resource_ids: %s, type: %s' %
                (subnet_id, resource_ids, resource_type))

    for resource_id in resource_ids:
        SubnetResource.insert(**{
            'id': 'subres-%s' % utils.generate_key(8),
            'subnet_id': subnet_id,
            'resource_id': resource_id,
            'resource_type': resource_type,
            'updated': datetime.datetime.utcnow(),
            'created': datetime.datetime.utcnow(),
        })

    logger.info('.create() OK.')
    return resource_ids


def remove(resource_ids, resource_type):
    """
    delete by resource_ids & resource_type
    """
    logger.info('.delete() begin, total len is: %d' % len(resource_ids))

    subnet_resources = []
    for resource_id in resource_ids:
        subres = get(resource_id=resource_id, resource_type=resource_type)
        subnet_resources.append(subres)

    for subres in subnet_resources:
        SubnetResource.delete(subres['id'])

    logger.info('.delete() OK.')


def get(subnet_id=None, resource_id=None, resource_type=None):
    logger.info('.get() begin, subnet_id: %s, resource_id: %s, type: %s' % (
                subnet_id, resource_id, resource_type))

    if subnet_id is None and resource_id is None:
        raise iaas_error.SubnetResourceNotFound(None, None)

    def where(t):
        _where = True
        if subnet_id:
            _where = filters.filter_subnet_ids(_where, t, [subnet_id])
        if resource_id:
            _where = filters.filter_resource_ids(_where, t, [resource_id])
        if resource_type:
            _where = filters.filter_resource_type(_where, t, resource_type)
        return _where

    subnet_resource = SubnetResource.first(where)
    if subnet_resource is None:
        raise iaas_error.SubnetResourceNotFound(subnet_id, resource_id)

    logger.info('.get() OK.')
    return subnet_resource


def count(subnet_id=None, resource_type=None):
    """
    count resources in the subnet. can filter by resource_type
    """
    def where(t):
        _where = True
        if subnet_id:
            _where = filters.filter_subnet_ids(_where, t, [subnet_id])
        if resource_type:
            _where = filters.filter_resource_type(_where, t, resource_type)
        return _where

    cnt = SubnetResource.count(where)
    return cnt


def limitation(subnet_ids=None, resource_ids=None, resource_type=None,
               offset=0, limit=10, reverse=True):
    def where(t):
        _where = True
        _where = filters.filter_subnet_ids(_where, t, subnet_ids)
        _where = filters.filter_resource_ids(_where, t, resource_ids)
        _where = filters.filter_resource_type(_where, t, resource_type)
        return _where

    logger.info('.limitation() begin')

    order_by = filters.order_by(reverse)
    page = SubnetResource.limitation_as_model(where,
                                              limit=limit,
                                              offset=offset,
                                              order_by=order_by)

    logger.info('.limitation() OK.')
    return page
