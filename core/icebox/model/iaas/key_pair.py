import datetime
from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas.openstack import api as op_api
from icebox.model.project import project as project_model
from densefog.model.job import job as job_model

from densefog import logger
logger = logger.getChild(__file__)

KEY_PAIR_STATUS_ACTIVE = 'active'
KEY_PAIR_STATUS_DELETED = 'deleted'


class KeyPair(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.key_pair

    def status_deletable(self):
        return self['status'] in [
            KEY_PAIR_STATUS_ACTIVE,
        ]

    def format(self):
        formated = {
            'keyPairId': self['id'],
            'projectId': self['project_id'],
            'name': self['name'],
            'description': self['description'],
            'status': self['status'],
            'publicKey': self['public_key'],
            'updated': self['updated'],
            'created': self['created'],
            'deleted': self['deleted'],
        }
        return formated


def create(project_id, name='', description='', public_key=None):
    logger.info('.create() begin')

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        project.must_have_enough_quota('key_pairs', 1)

        # assume create success.
        project.consume_quota('key_pairs', 1)

    key_pair_id = 'kp-%s' % utils.generate_key(8)

    try:
        # use icebox model id as openstack resource name
        keypair = op_api.do_create_keypair(project['op_project_id'],
                                           name=key_pair_id,
                                           public_key=public_key)
    except Exception as e:
        with base.open_transaction(db.DB):
            with base.lock_for_update():
                project = project_model.get(project_id)
            # but we failed.
            project.release_quota('key_pairs', 1)

        if hasattr(e, 'is_invalid') and e.is_invalid():
            raise iaas_error.KeyPairCreateInvalidPublicKeyError()
        raise

    else:
        key_pair_id = KeyPair.insert(**{
            'id': key_pair_id,
            'project_id': project_id,
            'name': name,
            'description': description,
            'status': KEY_PAIR_STATUS_ACTIVE,
            'public_key': keypair['public_key'],
            'updated': datetime.datetime.utcnow(),
            'created': datetime.datetime.utcnow(),
        })

        logger.info('.create() OK.')
        return key_pair_id, keypair.get('private_key', None)


def get(key_pair_id):
    logger.info('.get() begin, key_pair_id: %s' % key_pair_id)
    key_pair = KeyPair.get_as_model(key_pair_id)
    if key_pair is None:
        raise iaas_error.KeyPairNotFound(key_pair_id)

    logger.info('.get() OK.')
    return key_pair


def _pre_delete(project, key_pair_ids):
    key_pairs = []
    for key_pair_id in key_pair_ids:
        with base.lock_for_update():
            key_pair = get(key_pair_id)

        key_pair.must_belongs_project(project['id'])
        if not key_pair.status_deletable():
            raise iaas_error.KeyPairCanNotDelete(key_pair_id)

        key_pairs.append(key_pair)

    return key_pairs


@base.transaction
def delete(project_id, key_pair_ids):
    logger.info('.delete() begin, total count: %s, key_pair_ids: %s' %
                (len(key_pair_ids), key_pair_ids))
    with base.lock_for_update():
        project = project_model.get(project_id)

    key_pairs = _pre_delete(project, key_pair_ids)

    for key_pair in key_pairs:
        KeyPair.update(key_pair['id'], **{
            'status': KEY_PAIR_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    project.release_quota('key_pairs', len(key_pair_ids))

    logger.info('.delete() OK.')
    job_model.create(
        action='EraseKeyPairs',
        params={
            'resource_ids': key_pair_ids
        },
        run_at=utils.seconds_later(10),   # as fast as possible
        try_period=10)


def modify(project_id, key_pair_id, name=None, description=None):
    logger.info('.modify() begin, key_pair_id: %s' % key_pair_id)

    key_pair = get(key_pair_id)
    key_pair.must_belongs_project(project_id)

    if name is None:
        name = key_pair['name']

    if description is None:
        description = key_pair['description']

    KeyPair.update(key_pair_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')

    key_pair = get(key_pair_id)
    return key_pair


def limitation(key_pair_ids=None, status=None, project_ids=None,
               search_word=None, offset=0, limit=10, reverse=True):
    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, key_pair_ids)
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filters.filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() begin')
    page = KeyPair.limitation_as_model(where,
                                       limit=limit,
                                       offset=offset,
                                       order_by=filters.order_by(reverse))
    logger.info('.limitation() OK.')
    return page


def erase(key_pair_id):
    logger.info('.erase() begin, key_pair_id: %s' % key_pair_id)

    key_pair = get(key_pair_id)

    if key_pair['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if key_pair['status'] == KEY_PAIR_STATUS_DELETED:
        op_api.do_delete_keypair(key_pair_id)

        KeyPair.update(key_pair_id, **{
            'ceased': datetime.datetime.utcnow(),
        })
        logger.info('.erase() OK.')

    else:
        logger.warn('key_pair status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
