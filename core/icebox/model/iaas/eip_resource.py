import datetime
from densefog import db
from densefog.common import utils
from densefog.model import base
from icebox.model.iaas import error as iaas_error

from densefog import logger
logger = logger.getChild(__file__)


class EipResource(base.BaseModel):

    @classmethod
    def db(cls):
        return db.DB.eip_resource


def create(eip_id, resource_id, resource_type):
    logger.info('.create() begin')
    logger.info('eip_id: %s, resource_type: %s, resource_id: %s' %
                (eip_id, resource_type, resource_id))

    eip_resource_id = EipResource.insert(**{
        'id': 'er-%s' % utils.generate_key(8),
        'eip_id': eip_id,
        'resource_id': resource_id,
        'resource_type': resource_type,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })

    logger.info('.create() OK.')
    return eip_resource_id


def delete(eip_id=None, resource_id=None):
    logger.info('.delete() begin, resource_id: %s.' % resource_id)

    eip_resource = get(eip_id, resource_id)
    EipResource.delete(eip_resource['id'])

    logger.info('.delete() OK.')


def get(eip_id=None, resource_id=None):
    logger.info('.get() begin')

    if eip_id is None and resource_id is None:
        raise iaas_error.EipResourceNotFound((None, None))

    where = {}
    if eip_id:
        where['eip_id'] = eip_id
    if resource_id:
        where['resource_id'] = resource_id

    eip_resource = EipResource.first(where)
    if eip_resource is None:
        raise iaas_error.EipResourceNotFound((eip_id, resource_id))

    logger.info('.get() OK.')
    return eip_resource


def relations_from_instances(instance_ids):
    """
    caution: eip_resource.resource_id must be unique globally.

    return:
    {
        instance_id: eip_id or None  # none if no relations.
    }


    """
    logger.info('.relations_from_instances() begin')
    if not instance_ids:
        return {}

    SQL = """
        SELECT a.id as instance_id,
               b.eip_id as eip_id
        FROM   instance as a LEFT JOIN eip_resource as b
        ON     a.id = b.resource_id
        WHERE  a.id IN %s;
    """

    in_clause = "("
    in_clause += ",".join(["'%s'" % r for r in instance_ids])
    in_clause += ")"

    results = {}

    sql = SQL % (in_clause)
    logger.debug('EipResource.db().execute sql: %s' % sql)
    rows = EipResource.db().execute(sql)
    logger.debug('got total rows: %s' % len(rows))
    for r in rows:
        results[r['instance_id']] = r['eip_id']

    logger.info('.relations_from_instances() OK.')
    return results


def relations_from_eips(eip_ids):
    """
    return:
    {
        eip_id: (resource_type, resource_id) or (None, None) # if no relations
    }
    """
    logger.info('.relations_from_eips() begin')
    if not eip_ids:
        return {}

    SQL = """
        SELECT a.id as eip_id,
               b.resource_type as resource_type,
               b.resource_id as resource_id
        FROM  eip as a LEFT JOIN eip_resource as b
        ON    a.id = b.eip_id
        WHERE a.id IN %s;
    """
    in_clause = "("
    in_clause += ",".join(["'" + e + "'" for e in eip_ids])
    in_clause += ")"

    results = {}

    sql = SQL % (in_clause)
    logger.debug('EipResource.db().execute sql: %s' % sql)
    rows = EipResource.db().execute(sql)
    logger.debug('got total rows: %s' % len(rows))
    for r in rows:
        results[r['eip_id']] = (r['resource_type'], r['resource_id'])

    logger.info('.relations_from_eips() OK.')
    return results
