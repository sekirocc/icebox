import datetime
from densefog import db
from densefog.common import utils
from icebox.model.project import error
from densefog.model import base
from densefog.model import filters

from densefog import logger
logger = logger.getChild(__file__)


class AccessKey(base.ProjectModel):

    @classmethod
    def db(cls):
        return db.DB.access_key


MAX_EXPIRE_TIME = '2116-11-11T11:11:11Z'


def max_expire_time():
    return utils.parse_iso8601(MAX_EXPIRE_TIME)


def create(project_id, key, secret, expire_at=None):
    logger.info('.create() start. ')

    if expire_at is None:
        expire_at = max_expire_time()

    if isinstance(expire_at, basestring):
        expire_at = utils.parse_iso8601(expire_at)

    try:
        access_key_id = AccessKey.insert(**{
            'project_id': project_id,
            'key': key,
            'secret': secret,
            'deleted': 0,
            'expire_at': expire_at,
            'created': datetime.datetime.utcnow(),
            'updated': datetime.datetime.utcnow(),
        })
    except Exception as e:
        if 'Duplicate entry' in str(e):
            # raise error.AccessKeyDuplicated(key)
            # currently different service may use same endpoint,
            # like los and l2b.
            # so same access key sync request may be called twice.
            # we need to seperate endpoint for different service in feature.
            logger.exception('.create() duplicate access_key %s. ' % key)
        else:
            raise
    else:
        logger.info('.create() OK. ')
        return access_key_id


def check(key, signature, params):
    logger.info('.check() start. ')

    access_key = AccessKey.first_as_model(lambda t: t.key == key)
    if access_key is None:
        raise error.AccessKeyInvalid(key)
    if access_key['secret'] != signature:
        raise error.AccessKeyInvalid(key)

    now = datetime.datetime.utcnow()
    if access_key['expire_at'] and access_key['expire_at'] < now:
        raise error.AccessKeyExpired(key)

    logger.info('.check() OK. ')
    return access_key['project_id']


def delete(project_id, keys):
    logger.info('.delete() start. total count: %s' % len(keys))
    access_keys = []
    for key in keys:
        try:
            access_key = get(key)
            access_key.must_belongs_project(project_id)
            access_keys.append(access_key)
        except error.AccessKeyNotFound:
            # ignore access key not found. all we want is delete the key,
            # if it is not there, that's fine.
            pass

    for access_key in access_keys:
        AccessKey.update(access_key['id'], **{
            'deleted': 1,
            'updated': datetime.datetime.utcnow(),
        })

    logger.info('.delete() OK. ')


def get(key):
    logger.info('.get() start.')
    access_key = AccessKey.first_as_model(lambda t: t.key == key)
    if access_key is None:
        raise error.AccessKeyNotFound(key)

    logger.info('.get() OK.')
    return access_key


def limitation(project_ids=None, keys=None, offset=0, limit=10, reverse=True):
    def where(t):
        _where = True
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filters.filter_access_keys(_where, t, keys)
        return _where

    logger.info('.limitation() start.')
    page = AccessKey.limitation(where,
                                offset=offset,
                                limit=limit,
                                order_by=filters.order_by(reverse))

    logger.info('.limitation() OK.')
    return page
