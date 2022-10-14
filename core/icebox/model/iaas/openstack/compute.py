import novaclient
from novaclient import client as nova_client
from icebox.model.iaas.openstack import constants
from icebox.model.iaas.openstack import identify
from icebox.model.iaas.openstack import cache_openstack_client

SERVER_STATUS_ACTIVE = 'ACTIVE'
SERVER_STATUS_BUILDING = 'BUILDING'
SERVER_STATUS_DELETED = 'DELETED'
SERVER_STATUS_ERROR = 'ERROR'
SERVER_STATUS_HARD_REBOOT = 'HARD_REBOOT'
SERVER_STATUS_MIGRATING = 'MIGRATING'
SERVER_STATUS_PASSWORD = 'PASSWORD'
SERVER_STATUS_PAUSED = 'PAUSED'
SERVER_STATUS_REBOOT = 'REBOOT'
SERVER_STATUS_REBUILD = 'REBUILD'
SERVER_STATUS_RESCUED = 'RESCUED'
SERVER_STATUS_RESIZED = 'RESIZED'
SERVER_STATUS_REVERT_RESIZE = 'REVERT_RESIZE'
SERVER_STATUS_SOFT_DELETED = 'SOFT_DELETED'
SERVER_STATUS_STOPPED = 'STOPPED'
SERVER_STATUS_SUSPENDED = 'SUSPENDED'
SERVER_STATUS_UNKNOWN = 'UNKNOWN'
SERVER_STATUS_VERIFY_RESIZE = 'VERIFY_RESIZE'

SERVER_TASK_STATE_SCHEDULING = 'scheduling'
SERVER_TASK_STATE_BLOCK_DEVICE_MAPPING = 'block_device_mapping'
SERVER_TASK_STATE_NETWORKING = 'networking'
SERVER_TASK_STATE_SPAWNING = 'spawning'
SERVER_TASK_STATE_IMAGE_SNAPSHOT = 'image_snapshot'
SERVER_TASK_STATE_IMAGE_SNAPSHOT_PENDING = 'image_snapshot_pending'
SERVER_TASK_STATE_IMAGE_PENDING_UPLOAD = 'image_pending_upload'
SERVER_TASK_STATE_IMAGE_UPLOADING = 'image_uploading'
SERVER_TASK_STATE_IMAGE_BACKUP = 'image_backup'
SERVER_TASK_STATE_UPDATING_PASSWORD = 'updating_password'
SERVER_TASK_STATE_RESIZE_PREP = 'resize_prep'
SERVER_TASK_STATE_RESIZE_MIGRATING = 'resize_migrating'
SERVER_TASK_STATE_RESIZE_MIGRATED = 'resize_migrated'
SERVER_TASK_STATE_RESIZE_FINISH = 'resize_finish'
SERVER_TASK_STATE_RESIZE_REVERTING = 'resize_reverting'
SERVER_TASK_STATE_RESIZE_CONFIRMING = 'resize_confirming'
SERVER_TASK_STATE_REBOOTING = 'rebooting'
SERVER_TASK_STATE_REBOOT_PENDING = 'reboot_pending'
SERVER_TASK_STATE_REBOOT_STARTED = 'reboot_started'
SERVER_TASK_STATE_REBOOTING_HARD = 'rebooting_hard'
SERVER_TASK_STATE_REBOOT_PENDING_HARD = 'reboot_pending_hard'
SERVER_TASK_STATE_REBOOT_STARTED_HARD = 'reboot_started_hard'
SERVER_TASK_STATE_PAUSING = 'pausing'
SERVER_TASK_STATE_UNPAUSING = 'unpausing'
SERVER_TASK_STATE_SUSPENDING = 'suspending'
SERVER_TASK_STATE_RESUMING = 'resuming'
SERVER_TASK_STATE_POWERING_OFF = 'powering-off'
SERVER_TASK_STATE_POWERING_ON = 'powering-on'
SERVER_TASK_STATE_RESCUING = 'rescuing'
SERVER_TASK_STATE_UNRESCUING = 'unrescuing'
SERVER_TASK_STATE_REBUILDING = 'rebuilding'
SERVER_TASK_STATE_REBUILD_BLOCK_DEVICE_MAPPING = 'rebuild_block_device_mapping'
SERVER_TASK_STATE_REBUILD_SPAWNING = 'rebuild_spawning'
SERVER_TASK_STATE_MIGRATING = 'migrating'
SERVER_TASK_STATE_DELETING = 'deleting'
SERVER_TASK_STATE_SOFT_DELETING = 'soft-deleting'
SERVER_TASK_STATE_RESTORING = 'restoring'
SERVER_TASK_STATE_SHELVING = 'shelving'
SERVER_TASK_STATE_SHELVING_IMAGE_PENDING_UPLOAD = \
    'shelving_image_pending_upload'
SERVER_TASK_STATE_SHELVING_IMAGE_UPLOADING = 'shelving_image_uploading'
SERVER_TASK_STATE_SHELVING_OFFLOADING = 'shelving_offloading'
SERVER_TASK_STATE_UNSHELVING = 'unshelving'

SERVER_POWER_STATE_NO_STATE = 0
SERVER_POWER_STATE_RUNNING = 1
SERVER_POWER_STATE_BLOCKED = 2
SERVER_POWER_STATE_PAUSED = 3
SERVER_POWER_STATE_SHUTDOWN = 4
SERVER_POWER_STATE_SHUTOFF = 5
SERVER_POWER_STATE_CRASHED = 6
SERVER_POWER_STATE_SUSPENDED = 7
SERVER_POWER_STATE_FAILED = 8
SERVER_POWER_STATE_BUILDING = 9

HYPERVISOR_STATUS_ENABLED = 'enabled'
HYPERVISOR_STATUS_DISABLED = 'disabled'
HYPERVISOR_STATE_UP = 'up'
HYPERVISOR_STATE_DOWN = 'down'


@cache_openstack_client('compute')
def client(project_id=None):
    session = identify.client(project_id).session
    c = nova_client.Client('2.1', session=session)

    return c


def create_keypair(project_id, name, public_key=None):
    c = client(project_id)
    k = c.keypairs.create(name='%s%s' % (constants.NAME_PREFIX, name),
                          public_key=public_key)

    if public_key:
        return {
            'public_key': k.public_key,
            'fingerprint': k.fingerprint,
        }
    else:
        return {
            'public_key': k.public_key,
            'private_key': k.private_key,
            'fingerprint': k.fingerprint,
        }


def delete_keypair(name):
    c = client()
    c.keypairs.delete(key='%s%s' % (constants.NAME_PREFIX, name))


def list_keypairs():
    c = client()
    keypairs = c.keypairs.list()
    return [{
        'fingerprint': k.fingerprint,
        'public_key': k.public_key,
    } for k in keypairs if k.name.startswith(
        constants.NAME_PREFIX)]


def list_hypervisors():
    c = client()
    hypervisors = c.hypervisors.findall()
    return [{
        'id': h.id,
        'current_workload': h.current_workload,
        'disk_available_least': h.disk_available_least,
        'free_disk_gb': h.free_disk_gb,
        'free_ram_mb': h.free_ram_mb,
        'host_ip': h.host_ip,
        'hypervisor_hostname': h.hypervisor_hostname,
        'hypervisor_type': h.hypervisor_type,
        'hypervisor_version': h.hypervisor_version,
        'local_gb': h.local_gb,
        'local_gb_used': h.local_gb_used,
        'memory_mb': h.memory_mb,
        'memory_mb_used': h.memory_mb_used,
        'running_vms': h.running_vms,
        'state': h.state,
        'status': h.status,
        'vcpus': h.vcpus,
        'vcpus_used': h.vcpus_used
    } for h in hypervisors]


def _extract_server(s):
    return {
        'id': s.id,
        'status': s.status,
        'updated': s.updated,
        'user_id': s.user_id,
        'project_id': s.tenant_id,
        'metadata': s.metadata,
        'name': s.name,
        'hostId': s.hostId,
        'addresses': s.addresses,
        'config_drive': s.config_drive,
        'flavor': s.flavor,
        'image': s.image,
        'host': getattr(s, 'OS-EXT-SRV-ATTR:host'),
        'power_state': getattr(s, 'OS-EXT-STS:power_state'),
        'task_state': getattr(s, 'OS-EXT-STS:task_state'),
        'vm_state': getattr(s, 'OS-EXT-STS:vm_state'),
    }


def create_server(project_id, name,
                  image_id, flavor_id, nics,
                  key_name, user_data,
                  block_device_mapping_v2=None,
                  instance_count=1, password=None,
                  meta=None):
    c = client(project_id)
    if key_name:
        key_name = '%s%s' % (constants.NAME_PREFIX, key_name)
    s = c.servers.create(name=name,
                         image=image_id,
                         flavor=flavor_id,
                         userdata=user_data,
                         key_name=key_name,
                         nics=nics,
                         min_count=instance_count,
                         admin_pass=password,
                         security_groups=None,
                         block_device_mapping_v2=block_device_mapping_v2,
                         availability_zone=None,
                         disk_config=None,
                         config_drive=None,
                         meta=meta)
    return _extract_server(s)


def start_server(server_id):
    c = client()
    c.servers.start(server_id)


def stop_server(server_id):
    c = client()
    c.servers.stop(server_id)


def delete_server(server_id):
    c = client()
    c.servers.delete(server_id)


def reboot_server(server_id, reboot_type):
    c = client()
    c.servers.reboot(server_id, reboot_type=reboot_type)


def change_password(server_id, password):
    c = client()
    c.servers.change_password(server_id, password)


def change_keypair(server_id, key_name):
    c = client()
    url = '/servers/%s/action' % server_id
    body = {
        'changeKeypair': {
            'keypairName': '%s%s' % (constants.NAME_PREFIX, key_name)
        }
    }
    c.servers.api.client.post(url, body=body)


def get_vnc_console(server_id):
    c = client()
    vnc = c.servers.get_vnc_console(server_id, 'novnc')
    return {
        'type': vnc['console']['type'],
        'url': vnc['console']['url'],
    }


def get_console_output(server_id):
    c = client()
    output = c.servers.get_console_output(server_id)
    return output


def rebuild_server(server_id, image_id, name,
                   key_name=None, password=None,
                   meta=None):
    c = client()

    params = {}

    if key_name:
        params['key_name'] = '%s%s' % (constants.NAME_PREFIX, key_name)
    if password:
        params['password'] = password
    if meta:
        params['meta'] = meta

    c.servers.rebuild(server=server_id,
                      image=image_id,
                      name=name,
                      **params)


def resize_server(server_id, flavor_id):
    c = client()
    c.servers.resize(server_id, flavor_id)


def confirm_server_resize(server_id):
    c = client()
    c.servers.confirm_resize(server_id)


def get_server(server_id):
    c = client()
    s = c.servers.get(server_id)
    return _extract_server(s)


# def list_servers(project_id=None, status=None, marker=None, limit=None):
#     """
#     DONOT USE THIS API
#     UN-STABLE!!
#     """
#     c = client()
#     search_opts = {}
#     if project_id is None:
#         search_opts['all_tenants'] = True
#     else:
#         search_opts['tenant_id'] = project_id
#     search_opts['status'] = status

#     servers = c.servers.list(detailed=True,
#                              search_opts=search_opts,
#                              marker=marker,
#                              limit=limit)

#     return [_extract_server(s) for s in servers
#             if s.name.startswith(constants.NAME_PREFIX)]


def create_image(project_id, server_id, name):
    """
    create image from server.
    param project_id is IMPORTANT, which scope the image to THIS project.
    server_id should also belongs to THIS project.
    """
    c = client(project_id)
    image_id = c.servers.create_image(server_id, name)
    return str(image_id)


def list_security_groups(project_id=None):
    c = client()
    filters = {}
    if project_id:
        filters['tenant_id'] = project_id
    security_groups = c.security_groups.findall(**filters)
    return [{
        'id': s.id,
        'project_id': s.tenant_id,
        'name': s.name,
        'description': s.description,
        'rules': s.rules,
    } for s in security_groups if s.name.startswith(
        constants.NAME_PREFIX) or s.name == 'default']


def delete_flavor(flavor_id):
    c = client()
    c.flavors.delete(flavor=flavor_id)


def find_flavor(instance_type_id):
    c = client()
    try:
        f = c.flavors.find(id=instance_type_id)
        return {
            'id': f.id,
            'name': f.name,
            'vcpus': f.vcpus,
            'ram': f.ram,
            'swap': f.swap,
            'disk': f.disk,
            'is_public': f.is_public
        }
    except novaclient.exceptions.NotFound:
        return None


def create_flavor(name, ram, vcpus, disk, flavorid='auto',
                  ephemeral=0, swap=0, is_public=True):
    c = client()
    f = c.flavors.create(name='%s%s' % (constants.NAME_PREFIX, name),
                         ram=ram,
                         vcpus=vcpus,
                         disk=disk,
                         flavorid=flavorid,
                         ephemeral=ephemeral,
                         swap=swap,
                         is_public=is_public)
    return {
        'id': f.id,
        'name': f.name,
        'vcpus': f.vcpus,
        'ram': f.ram,
        'swap': f.swap,
        'disk': f.disk,
        'is_public': f.is_public
    }


def list_flavors():
    c = client()
    flavors = c.flavors.findall(is_public=True)
    return [{
        'id': f.id,
        'name': f.name,
        'vcpus': f.vcpus,
        'ram': f.ram,
        'swap': f.swap,
        'disk': f.disk,
        'is_public': f.is_public
    } for f in flavors if f.name.startswith(
        constants.NAME_PREFIX)]


def update_flavor_quota(flavor_id,
                        disk_read_iops_sec,
                        disk_write_iops_sec,
                        disk_read_bytes_sec,
                        disk_write_bytes_sec,
                        vif_inbound_average,
                        vif_outbound_average):
    c = client()
    flavor = c.flavors.get(flavor_id)
    flavor.set_keys({
        'quota:disk_read_iops_sec': disk_read_iops_sec,
        'quota:disk_write_iops_sec': disk_write_iops_sec,
        'quota:disk_read_bytes_sec': disk_read_bytes_sec,
        'quota:disk_write_bytes_sec': disk_write_bytes_sec,
        'quota:vif_inbound_average': vif_inbound_average,
        'quota:vif_outbound_average': vif_outbound_average,
    })


def get_quota(project_id):
    c = client()
    quota = c.quotas.get(project_id)
    return {
        'cores': quota.cores,
        'fixed_ips': quota.fixed_ips,
        'floating_ips': quota.floating_ips,
        'injected_file_content_bytes': quota.injected_file_path_bytes,
        'injected_file_path_bytes': quota.injected_file_path_bytes,
        'injected_files': quota.injected_files,
        'instances': quota.instances,
        'key_pairs': quota.key_pairs,
        'metadata_items': quota.metadata_items,
        'ram': quota.ram,
        'security_group_rules': quota.security_group_rules,
        'security_groups': quota.security_groups,
        'server_group_members': quota.server_group_members,
        'server_groups': quota.server_groups
    }


def update_quota(project_id, **kwargs):
    c = client()
    c.quotas.update(project_id, **kwargs)


def create_server_volume(server_id, volume_id):
    """
    Attach a volume identified by the volume ID to the given server ID
    """
    c = client()
    c.volumes.create_server_volume(server_id, volume_id)


def delete_server_volume(server_id, volume_id):
    """
    Detach a volume identified by the attachment ID from the given server
    """
    c = client()
    c.volumes.delete_server_volume(server_id, volume_id)


def interface_detach(server_id, port_id):
    """
    Detach an port interface
    """
    c = client()
    c.servers.interface_detach(server_id, port_id)
