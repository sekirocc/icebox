from icebox import model
import datetime
import traceback

from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from densefog.model.job import job as job_model

from icebox import config
from icebox.model.project import project as project_model
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import volume as volume_model
from icebox.model.iaas.openstack import block as block_provider
from icebox.model.iaas.openstack import error as op_error

from densefog import logger
logger = logger.getChild(__file__)

SNAPSHOT_STATUS_PENDING = 'pending'
SNAPSHOT_STATUS_ACTIVE = 'active'
SNAPSHOT_STATUS_ERROR = 'error'
SNAPSHOT_STATUS_DELETED = 'deleted'
SNAPSHOT_STATUS_CEASED = 'ceased'

SNAPSHOT_STATE_MAP = {
    block_provider.SNAPSHOT_STATUS_CREATING: SNAPSHOT_STATUS_PENDING,
    block_provider.SNAPSHOT_STATUS_AVAILABLE: SNAPSHOT_STATUS_ACTIVE,
    block_provider.SNAPSHOT_STATUS_DELETING: SNAPSHOT_STATUS_PENDING,
    block_provider.SNAPSHOT_STATUS_ERROR: SNAPSHOT_STATUS_ERROR,
    block_provider.SNAPSHOT_STATUS_ERROR_DELETING: SNAPSHOT_STATUS_ERROR,
}


class Snapshot(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.snapshot

    def status_deletable(self):
        return self['status'] in [
            SNAPSHOT_STATUS_ACTIVE,
            SNAPSHOT_STATUS_ERROR,
        ]

    def format(self):
        formated = {
            'snapshotId': self['id'],
            'projectId': self['project_id'],
            'name': self['name'],
            'description': self['description'],
            'size': self['size'],
            'volumeType': self['volume_type'],
            'status': self['status'],
            'updated': self['updated'],
            'created': self['created'],
            'deleted': self['deleted'],
            'ceased': self['ceased'],
        }
        return formated


def create(project_id, volume_id, name='', description='', count=1):
    logger.info('.create() begin, total count: %s' % count)

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        project.must_have_enough_quota('snapshots', count)

        # assume creations success.
        project.consume_quota('snapshots', count)

    op_project_id = project['op_project_id']

    volume = volume_model.get(volume_id)
    # TODO. volume should have some pre-condistions?
    # TODO. should lock volume??

    op_volume_id = volume['op_volume_id']

    creatings = []
    exceptions = []
    for i in range(count):
        snapshot_id = 'snpsht-%s' % utils.generate_key(8)

        try:
            provider_snapshot = block_provider.create_snapshot(
                project_id=op_project_id,
                volume_id=op_volume_id,
                # use icebox model id as openstack resource name
                name=snapshot_id,
                description=description)

        except Exception as e:
            stack = traceback.format_exc()  # noqa
            e = iaas_error.ProviderCreateSnapshotError(e, stack)

            exceptions.append({
                'snapshot': None,
                'exception': e
            })
        else:
            snapshot_id = Snapshot.insert(**{
                'id': snapshot_id,
                'op_snapshot_id': provider_snapshot['id'],
                'project_id': project_id,
                'name': name,
                'description': description,
                'size': volume['size'],
                'volume_type': volume['volume_type'],
                'status': SNAPSHOT_STATUS_PENDING,
                'updated': datetime.datetime.utcnow(),
                'created': datetime.datetime.utcnow(),
            })
            creatings.append(snapshot_id)

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)
        # release those failed.
        project.release_quota('snapshots', len(exceptions))

    logger.info('.create() OK. creatings: %s, exceptions: %s' %
                (len(creatings), len(exceptions)))

    return model.actions_job('CreateSnapshots',
                             project_id,
                             creatings,
                             exceptions)


def get(snapshot_id):
    logger.info('.get() begin, snapshot_id: %s' % snapshot_id)
    snapshot = Snapshot.get_as_model(snapshot_id)
    if snapshot is None:
        raise iaas_error.SnapshotNotFound(snapshot_id)

    logger.info('.get() OK.')
    return snapshot


def _pre_delete(project, snapshot_ids):
    snapshots = []
    for snapshot_id in snapshot_ids:
        with base.lock_for_update():
            snapshot = get(snapshot_id)

        snapshot.must_belongs_project(project['id'])
        if not snapshot.status_deletable():
            raise iaas_error.SnapshotCanNotDelete(snapshot_id)
        snapshots.append(snapshot)

    return snapshots


@base.transaction
def delete(project_id, snapshot_ids):
    """
    delete snapshots.
    """
    logger.info('.delete() begin, total count: %s, snapshot_ids: %s' %
                (len(snapshot_ids), snapshot_ids))

    with base.lock_for_update():
        project = project_model.get(project_id)

    snapshots = _pre_delete(project, snapshot_ids)

    for snapshot in snapshots:
        Snapshot.update(snapshot['id'], **{
            'status': SNAPSHOT_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    project.release_quota('snapshots', len(snapshot_ids))

    logger.info('.delete() OK.')

    job_model.create(
        action='EraseSnapshots',
        params={
            'resource_ids': snapshot_ids
        },
        run_at=utils.seconds_later(config.CONF.erase_delay),
        try_period=config.CONF.try_period)


def modify(project_id, snapshot_id, name=None, description=None):
    logger.info('.modify() begin.')

    snapshot = get(snapshot_id)
    snapshot.must_belongs_project(project_id)

    if name is None:
        name = snapshot['name']

    if description is None:
        description = snapshot['description']

    Snapshot.update(snapshot_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')

    snapshot = get(snapshot_id)
    return snapshot


def limitation(project_ids=None, status=None, snapshot_ids=None,
               search_word=None, offset=0, limit=10, reverse=True):
    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, snapshot_ids)
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filters.filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() begin.')
    page = Snapshot.limitation_as_model(where,
                                        limit=limit,
                                        offset=offset,
                                        order_by=filters.order_by(reverse))
    logger.info('.limitation() OK.')

    return page


def sync(snapshot_id):
    logger.info('.sync() begin.')
    snapshot = get(snapshot_id)

    try:
        provider_snapshot = block_provider.get_snapshot(snapshot['op_snapshot_id'])   # noqa
    except:
        Snapshot.update(snapshot_id, **{
            'status': SNAPSHOT_STATUS_ERROR,
            'updated': datetime.datetime.utcnow(),
        })
        raise

    provider_status = provider_snapshot['status']

    status = SNAPSHOT_STATE_MAP[provider_status]

    logger.info('snapshot status: (%s) => (%s) .' % (snapshot['status'], status))  # noqa

    Snapshot.update(snapshot_id, **{
        'status': status,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.sync() OK.')
    snapshot = get(snapshot_id)
    return snapshot


def erase(snapshot_id):
    logger.info('.sync() begin. snapshot_id: %s' % snapshot_id)

    snapshot = get(snapshot_id)

    if snapshot['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if snapshot['status'] == SNAPSHOT_STATUS_DELETED:
        try:
            block_provider.delete_snapshot(snapshot['op_snapshot_id'])
        except Exception as ex:
            if op_error.is_notfound(ex):
                pass
            else:
                trace = traceback.format_exc()
                raise iaas_error.ProviderDeleteSnapshotError(ex, trace)

        Snapshot.update(snapshot_id, **{
            'status': SNAPSHOT_STATUS_CEASED,
            'ceased': datetime.datetime.utcnow(),
        })
        logger.info('.sync() OK.')

    else:
        logger.warn('snapshot status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
