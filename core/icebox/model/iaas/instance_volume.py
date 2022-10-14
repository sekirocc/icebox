import datetime
from densefog import db
from densefog.model import base
from densefog.common import utils
from icebox.model.iaas import error as iaas_error

from densefog import logger
logger = logger.getChild(__file__)


class InstanceVolume(base.BaseModel):

    @classmethod
    def db(cls):
        return db.DB.instance_volume

    def format(self):
        formated = {
            'instanceId': self['instance_id'],
            'volumeId': self['volume_id'],
            'created': self['created'],
        }
        return formated


def create(volume_id, instance_id):
    logger.info('.create() begin volume_id: %s, instance_id: %s' %   # noqa
                (volume_id, instance_id))

    instance_volume_id = InstanceVolume.insert(**{
        'id': 'iv-%s' % utils.generate_key(8),
        'instance_id': instance_id,
        'volume_id': volume_id,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    logger.info('.create() OK.')
    return instance_volume_id


def delete(volume_id=None, instance_id=None):
    logger.info('.delete() begin. volume_id: %s, instance_id: %s' %   # noqa
                (volume_id, instance_id))
    instance_volume = get(volume_id, instance_id)
    InstanceVolume.delete(instance_volume['id'])
    logger.info('.delete() OK.')


def get(volume_id=None, instance_id=None):
    logger.info('.get() begin. volume_id: %s, instance_id: %s' %   # noqa
                (volume_id, instance_id))

    if not volume_id and not instance_id:
        raise iaas_error.InstanceVolumeNotFound((None, None))

    where = {}
    if volume_id:
        where['volume_id'] = volume_id
    if instance_id:
        where['instance_id'] = instance_id

    instance_volume = InstanceVolume.first(where)
    if instance_volume is None:
        raise iaas_error.InstanceVolumeNotFound((instance_id, volume_id))

    logger.info('.get() OK.')
    return instance_volume


def relations_from_instances(instance_ids):
    """
    return:
    {
        instance_id: [volume_id] or []  # empty list when no relations.
    }
    """
    logger.info('.relations_from_instances() begin')
    if not instance_ids:
        return {}

    SQL = """
        SELECT a.id as instance_id,
               b.volume_id as volume_id
        FROM   instance as a LEFT JOIN instance_volume as b
        ON     a.id = b.instance_id
        WHERE  a.id IN %s;
    """

    in_clause = "("
    in_clause += ",".join(["'%s'" % r for r in instance_ids])
    in_clause += ")"

    results = {}

    sql = SQL % (in_clause)
    logger.debug('InstanceVolume.db().execute sql: %s' % sql)
    rows = InstanceVolume.db().execute(sql)
    logger.debug('got total rows: %s' % len(rows))
    for r in rows:
        volume_ids = results.setdefault(r['instance_id'], [])
        if r['volume_id']:
            volume_ids.append(r['volume_id'])

    logger.info('.relations_from_instances() OK.')
    return results


def relations_from_volumes(volume_ids):
    """
    return:
    {
        volume_id: instance_id or None  # none if no relations
    }
    """
    logger.info('.relations_from_volumes() begin')
    if not volume_ids:
        return {}

    SQL = """
        SELECT a.id as volume_id,
               b.instance_id as instance_id
        FROM  volume as a LEFT JOIN instance_volume as b
        ON    a.id = b.volume_id
        WHERE a.id IN %s;
    """
    in_clause = "("
    in_clause += ",".join(["'" + v + "'" for v in volume_ids])
    in_clause += ")"

    results = {}

    sql = SQL % (in_clause)
    logger.debug('InstanceVolume.db().execute sql: %s' % sql)
    rows = InstanceVolume.db().execute(sql)
    logger.debug('got total rows: %s' % len(rows))
    for r in rows:
        results[r['volume_id']] = r['instance_id']

    logger.info('.relations_from_volumes() OK.')
    return results
