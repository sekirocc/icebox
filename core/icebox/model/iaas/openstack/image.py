import json
from glanceclient.v2 import client as glance_client
from icebox.model.iaas.openstack import identify
# from icebox.model.iaas.openstack import cache_openstack_client

IMAGE_STATUS_ACTIVE = 'active'
IMAGE_STATUS_SAVING = 'saving'
IMAGE_STATUS_QUEUED = 'queued'
IMAGE_STATUS_PENDING_DELETE = 'pending_delete'
IMAGE_STATUS_KILLED = 'killed'
IMAGE_STATUS_DELETED = 'deleted'
IMAGE_STATUS_DEACTIVATED = 'deactivated'


# @cache_openstack_client('image')
def client(project_id=None, endpoint=None):
    session = identify.client(project_id).session
    client = glance_client.Client(session=session)

    # use my own glance endpoint.
    # 'http://10.148.13.126:9292'
    if endpoint:
        client.http_client.endpoint_override = endpoint

    return client


def _extract_image(i):
    try:
        capshot_id = i.capshot_id
    except:
        capshot_id = None
    try:
        bdm = i.block_device_mapping
    except:
        bdm = json.dumps([])
    try:
        locations = i.locations
    except:
        locations = []

    return {
        'id': i.id,   # u'7d61be1a-6769-4355-9d5b-107f83b5dc6e',
        'name': i.name,   # u'cirros-0.3.4-x86_64-uec-kernel',
        'min_disk': i.min_disk,   # 0,
        'min_memory': i.min_ram,   # 0,
        'owner': i.owner,   # u'ca187564e43149af8262c88545bdfcf3',
        'protected': i.protected,   # False,
        # 'schema': i.schema,   # u'/v2/schemas/image',
        'size': i.size,   # 4979632,
        'checksum': i.checksum,   # u'8a40c862b5735975d82605c1dd395796',
        'container_format': i.container_format,   # u'aki',
        'disk_format': i.disk_format,   # u'aki',
        'file': i.file,   # u'/v2/images/7d61be1a-6769-4355-9d5b-107f83b5dc6e/file',   # noqa
        'status': i.status,   # u'active',
        'tags': i.tags,   # [],
        'created': i.created_at,   # u'2021-06-22T09:14:52Z',
        'updated': i.updated_at,   # u'2021-06-23T09:00:59Z',
        'virtual_size': i.virtual_size,   # None,
        'capshot_id': capshot_id,
        'block_device_mapping': bdm,
        'locations': locations,
    }


def list_images(project_id=None):
    """
    list images scoped to this project (private images).
    if project is None, return public images

    """
    c = client()

    filters = {}
    if project_id:
        filters['owner'] = project_id
        filters['visibility'] = 'private,shared'
    else:
        filters['visibility'] = 'public'

    images = c.images.list(filters=filters)

    return [_extract_image(i) for i in images]


def get_image(image_id):
    """
    get image detail.
    it can get everyone's image detail
    """
    c = client()
    i = c.images.get(image_id)

    return _extract_image(i)


def delete_image(image_id):
    """
    delete image.
    it can delete everyone's image
    """
    c = client()
    c.images.delete(image_id)


def create_image(project_id, name, min_disk, min_memory, capshot_id=None):
    """
    create image.
    """
    c = client()
    properties = {
        'hw_cpu_sockets': '2',
        'hw_disk_bus': 'scsi',
        'hw_qemu_guest_agent': 'yes',
        'hw_scsi_model': 'virtio-scsi',
    }
    if capshot_id:
        properties['capshot_id'] = capshot_id

    i = c.images.create(owner=project_id,
                        name=name,
                        container_format='ovf',
                        disk_format='raw',
                        min_disk=min_disk,
                        min_ram=min_memory,
                        **properties)

    return _extract_image(i)


def add_image_location(image_id, url, metadata={}):
    """
    add a rbd location to image.
    """
    c = client()
    i = c.images.add_location(image_id, url, metadata)

    return _extract_image(i)


def delete_image_location(image_id, url):
    """
    add a rbd location to image.
    """
    c = client()
    c.images.delete_locations(image_id, set([url]))
