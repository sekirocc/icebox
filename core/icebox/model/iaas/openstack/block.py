from cinderclient import client as cinder_client
from icebox.model.iaas.openstack import constants
from icebox.model.iaas.openstack import identify
from icebox.model.iaas.openstack import cache_openstack_client

VOLUME_STATUS_CREATING = 'creating'
VOLUME_STATUS_EXTENDING = 'extending'
VOLUME_STATUS_AVAILABLE = 'available'
VOLUME_STATUS_ATTACHING = 'attaching'
VOLUME_STATUS_DETACHING = 'detaching'
VOLUME_STATUS_IN_USE = 'in-use'
VOLUME_STATUS_DELETING = 'deleting'
VOLUME_STATUS_ERROR = 'error'
VOLUME_STATUS_ERROR_DELETING = 'error_deleting'
VOLUME_STATUS_BACKING_UP = 'backing-up'
VOLUME_STATUS_RESTORING_BACKUP = 'restoring-backup'
VOLUME_STATUS_ERROR_RESTORING = 'error_restoring'
VOLUME_STATUS_ERROR_EXTENDING = 'error_extending'

SNAPSHOT_STATUS_CREATING = 'creating'
SNAPSHOT_STATUS_AVAILABLE = 'available'
SNAPSHOT_STATUS_DELETING = 'deleting'
SNAPSHOT_STATUS_ERROR = 'error'
SNAPSHOT_STATUS_ERROR_DELETING = 'error_deleting'


@cache_openstack_client('block')
def client(project_id=None):
    session = identify.client(project_id).session
    c = cinder_client.Client(2, session=session)
    return c


def update_quota(project_id, **kwargs):
    c = client()
    c.quotas.update(project_id, **kwargs)


def _extract_volume(v):
    volume = {
        'id': v.id,
        'created': v.created_at,
        'status': v.status,
        'attachments': v.attachments,
        'availability_zone': v.availability_zone,
        'bootable': v.bootable == 'true',
        'description': v.description,
        'name': v.name,
        'encrypted': v.encrypted,
        'metadata': v.metadata,
        'multiattach': v.multiattach == 'true',
        'size': v.size,
        'snapshot_id': v.snapshot_id,
        'source_volid': v.source_volid,
        'volume_type': v.volume_type,
        'host': getattr(v, 'os-vol-host-attr:host'),
    }

    return volume


def list_volumes(project_id=None):
    c = client()

    search_opts = {}
    if project_id is None:
        search_opts['all_tenants'] = True
    else:
        search_opts['tenant_id'] = project_id

    volumes = c.volumes.list(search_opts=search_opts)
    return [_extract_volume(v) for v in volumes
            if v.name.startswith(constants.NAME_PREFIX)]


def create_volume(size,  # Size of volume in GB
                  name,
                  project_id=None,
                  volume_type=None,       # use in multi backends.
                  snapshot_id=None,
                  image_ref=None,  # create volume from image
                  ):
    c = client(project_id)
    v = c.volumes.create(size,
                         name='%s%s' % (constants.NAME_PREFIX, name),
                         volume_type=volume_type,
                         snapshot_id=snapshot_id,
                         imageRef=image_ref)

    return _extract_volume(v)


def delete_volume(volume_id):
    c = client()
    c.volumes.delete(volume_id)


def get_volume(volume_id):
    c = client()
    v = c.volumes.get(volume_id)

    return _extract_volume(v)


def extend_volume(volume_id, new_size):
    c = client()
    c.volumes.extend(volume_id, new_size)


def _extract_snapshot(s):
    return {
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'volume_id': s.volume_id,
        'size': s.size,
        'status': s.status,
        'updated': s.updated_at,
        'created': s.created_at,
    }


def create_snapshot(project_id, volume_id, name, description=None):
    c = client(project_id)
    s = c.volume_snapshots.create(volume_id,
                                  force=True,
                                  name='%s%s' % (constants.NAME_PREFIX, name),
                                  description=description)
    return _extract_snapshot(s)


def delete_snapshot(snapshot_id):
    c = client()
    c.volume_snapshots.delete(snapshot_id)


def get_snapshot(snapshot_id):
    c = client()
    s = c.volume_snapshots.get(snapshot_id)

    return _extract_snapshot(s)


def list_snapshots(project_id=None):
    c = client()

    search_opts = {}
    if project_id is None:
        search_opts['all_tenants'] = True
    else:
        search_opts['tenant_id'] = project_id

    snapshots = c.volume_snapshots.list(search_opts=search_opts)

    return [_extract_snapshot(s) for s in snapshots
            if s.name.startswith(constants.NAME_PREFIX)]


def _extract_capshot(cp):
    return {
        'id': cp.id,
        'name': cp.name,
        'description': cp.description,
        'volume_id': cp.volume_id,
        'snapshot_id': cp.snapshot_id,
        'provider_location': cp.provider_location,
        'size': cp.size,
        'status': cp.status,
        'updated': cp.updated_at,
        'created': cp.created_at,
    }


def create_capshot(project_id, snapshot_id):
    c = client(project_id)
    cp = c.volume_capshots.create(snapshot_id)

    return _extract_capshot(cp)


def get_capshot(capshot_id):
    c = client()
    cp = c.volume_capshots.get(capshot_id)

    return _extract_capshot(cp)


def delete_capshot(capshot_id):
    c = client()
    c.volume_capshots.delete(capshot_id)
