import json
import datetime
from icebox.api.public import switch as public_switch
from icebox.api.manage import switch as manage_switch
from densefog.server import create_api
from densefog.server import create_worker
from densefog.common import utils
from icebox.model.iaas import image as image_model
from densefog.model.job import job as job_model
from icebox.model.project import project as project_model
from densefog.model.journal import operation as operation_model
from icebox.model.project import access_key as access_key_model
from icebox.model.iaas import subnet as subnet_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import port_forwarding as port_forwarding_model
from icebox.model.iaas import instance_type as instance_type_model
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import key_pair as key_pair_model
from icebox.model.iaas import instance_volume as instance_volume_model
from icebox.model.iaas import volume as volume_model
from icebox.model.iaas import snapshot as snapshot_model
from icebox.model.iaas import eip as eip_model
from icebox.model.iaas import eip_resource as eip_resource_model
from icebox.model.iaas import subnet_resource as subres_model
from icebox.model.iaas import floatingip as floatingip_model
from icebox.model.iaas import hypervisor as hypervisor_model


instance_id_a = 'i-123'
project_id_a = 't-123'
image_id_a = 'img-123'
image_name_a = 'img-name-ab'
instance_type_id_a = 'itp-123'
network_id_a = 'net-123'
cidr_a = '192.168.0.0/24'
ip_start_a = '192.168.0.1'
ip_end_a = '192.168.0.254'
port_forwarding_id_a = 'pf-123'
inside_address_a = '192.168.10.1'
floatingip_id_a = 'fip-123'
ip_a = '192.168.200.200'
subnet_id_a = 'snt-123'
key_pair_id_a = 'kp-123'
volume_id_a = 'v-123'
snapshot_id_a = 'snapshot-123'
eip_id_a = 'eip-123'
eip_resource_id_a = 'eip-resour-123'
access_key_a = 'access-key-a'
access_secret_a = 'access-secret-a'
hypervisor_id_a = 'hyper-123'

job_id_a = 'job_id-123'
action_a = 'Sync'
params_a = json.dumps({})


def mock_nope(*args, **kwargs):
    return None


def insert_snapshot(project_id=project_id_a,
                    snapshot_id=snapshot_id_a,
                    status=snapshot_model.SNAPSHOT_STATUS_ACTIVE):

    snapshot_model.Snapshot.insert(**{
        'id': snapshot_id,
        'project_id': project_id,
        'status': status,
        'op_snapshot_id': utils.generate_key(36),
        'name': 'a_vol',
        'size': 1,
        'volume_type': volume_model.SUPPORTED_VOLUME_TYPES[0],
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })

    return snapshot_id


def insert_access_key(project_id=project_id_a,
                      access_key=access_key_a,
                      access_secret=access_secret_a):
    access_key_id = access_key_model.AccessKey.insert(**{
        'project_id': project_id,
        'key': access_key,
        'secret': access_secret,
        'deleted': 0,
        'expire_at': datetime.datetime.utcnow() + datetime.timedelta(days=365),   # noqa
        'created': datetime.datetime.utcnow(),
        'updated': datetime.datetime.utcnow(),
    })
    return access_key_id


def insert_key_pair(project_id=project_id_a,
                    key_pair_id=key_pair_id_a,
                    status=key_pair_model.KEY_PAIR_STATUS_ACTIVE):
    key_pair_id = key_pair_model.KeyPair.insert(**{
        'id': key_pair_id,
        'project_id': project_id,
        'name': 'kpair-name',
        'description': 'desc',
        'status': status,
        'public_key': '*' * 500,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return key_pair_id


def insert_instance_type(project_id=project_id_a,
                         instance_type_id=instance_type_id_a,
                         status=instance_type_model.INSTANCE_TYPE_STATUS_ACTIVE):  # noqa
    instance_type_id = instance_type_model.InstanceType.insert(**{
        'id': instance_type_id,
        'name': 'c1m1024',
        'description': '',
        'project_id': project_id,
        'op_flavor_id': utils.generate_uuid(),
        'vcpus': 1,
        'memory': 1024,
        'disk': 20,
        'status': status,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow()
    })
    return instance_type_id


def insert_image(project_id=project_id_a,
                 image_id=image_id_a,
                 image_name=image_name_a,
                 os_family=image_model.OS_UNKNOWN,
                 platform=image_model.PLATFORM_UNKNOWN,
                 processor_type=image_model.PROCESSOR_TYPE_32,
                 op_image_id=None,
                 status=image_model.IMAGE_STATUS_ACTIVE):
    op_image_id = op_image_id or utils.generate_uuid()
    image_id = image_model.Image.insert(**{
        'id': image_id,
        'name': image_name,
        'project_id': project_id,
        'description': '',
        'size': 0,
        'platform': platform,
        'os_family': os_family,
        'processor_type': processor_type,
        'min_vcpus': 1,
        'min_memory': 1024,
        'min_disk': 10,
        'status': status,
        'op_image_id': op_image_id,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return image_id


def insert_hypervisor(hypervisor_id=hypervisor_id_a,
                      op_hyper_id=None,
                      name=None,
                      status=hypervisor_model.HYPERVISOR_STATUS_ENABLED,
                      state=hypervisor_model.HYPERVISOR_STATE_UP):

    hypervisor_id = hypervisor_model.Hypervisor.insert(**{
        'id': hypervisor_id,
        'op_hyper_id': op_hyper_id or utils.generate_uuid(),
        'name': name or 'hyper-name',
        'current_workload': 3,
        'disk_available_least': 20,
        'free_disk_gb': 10,
        'free_ram_mb': 1024,
        'host_ip': '192.168.1.2',
        'hypervisor_type': 'kvm',
        'hypervisor_version': '2.0.0',
        'local_gb': 600,
        'local_gb_used': 500,
        'memory_mb': 10240,
        'memory_mb_used': 1024,
        'running_vms': 9,
        'state': state,
        'status': status,
        'vcpus': 60,
        'vcpus_used': 50,
        'description': '',
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return hypervisor_id


def insert_eip_resource(eip_resource_id=eip_resource_id_a,
                        eip_id=eip_id_a,
                        resource_id=instance_id_a,
                        resource_type=eip_model.RESOURCE_TYPE_INSTANCE):
    eip_resource_model.EipResource.insert(**{
        'id': eip_resource_id,
        'eip_id': eip_id,
        'resource_id': resource_id,
        'resource_type': resource_type,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return eip_resource_id


def insert_eip(project_id=project_id_a,
               eip_id=eip_id_a,
               address=None,
               op_floatingip_id=None,
               status=eip_model.EIP_STATUS_ACTIVE,
               bandwidth=eip_model.DEFAULT_BANDWIDTH):
    eip_model.Eip.insert(**{
        'id': eip_id,
        'op_floatingip_id': op_floatingip_id or utils.generate_key(36),
        'project_id': project_id,
        'name': 'eip-name',
        'description': 'eip-desc',
        'bandwidth': bandwidth,
        'status': status,
        'address': address or '',
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return eip_id


def insert_network(project_id=project_id_a,
                   network_id=network_id_a,
                   status=network_model.NETWORK_STATUS_PENDING):
    network_id = network_model.Network.insert(**{
        'id': network_id,
        'project_id': project_id,
        'name': 'netwk-name',
        'description': '',
        'status': status,
        'op_router_id': utils.generate_uuid(),
        'op_network_id': utils.generate_uuid(),
        'external_gateway_ip': '',
        'external_gateway_bandwidth': 0,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return network_id


def insert_port_forwarding(
    project_id=project_id_a,
    port_forwarding_id=port_forwarding_id_a,
    network_id=network_id_a,
    inside_address=inside_address_a,
    status=port_forwarding_model.PORT_FORWARDING_STATUS_ACTIVE
):
    port_forwarding_id = port_forwarding_model.PortForwarding.insert(**{
        'id': port_forwarding_id,
        'project_id': project_id,
        'network_id': network_id,
        'op_port_forwarding_id': utils.generate_uuid(),
        'op_router_id': utils.generate_uuid(),
        'protocol': 'tcp',
        'outside_port': 80,
        'inside_address': inside_address,
        'inside_port': 80,
        'name': 'a-port-forwarding',
        'description': 'a-desc',
        'status': status,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return port_forwarding_id


def insert_floatingip(
    floatingip_id=floatingip_id_a,
    ip=ip_a,
    status=floatingip_model.FLOATINGIP_STATUS_ACTIVE
):

    floatingip_id = floatingip_model.Floatingip.insert(**{
        'id': floatingip_id,
        'address': ip,
        'status': status,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return floatingip_id


def insert_floatingips():
    ips = ['192.168.200.1',
           '192.168.200.2',
           '192.168.200.3',
           '192.168.200.4',
           '192.168.200.5']
    for ip in ips:
        insert_floatingip(floatingip_id=utils.generate_key(10), ip=ip)


def insert_subnet_resources(subnet_id, resource_ids, resource_type):
    subres_ids = []
    for resource_id in resource_ids:
        subres_id = subres_model.SubnetResource.insert(**{
            'id': 'subres-' + utils.generate_key(8),
            'subnet_id': subnet_id,
            'resource_id': resource_id,
            'resource_type': resource_type,
            'updated': datetime.datetime.utcnow(),
            'created': datetime.datetime.utcnow(),
        })
        subres_ids.append(subres_id)

    return subres_ids


def insert_subnet(subnet_id=subnet_id_a,
                  project_id=project_id_a,
                  network_id=network_id_a,
                  cidr=cidr_a,
                  ip_start=ip_start_a,
                  ip_end=ip_end_a,
                  status=subnet_model.SUBNET_STATUS_ACTIVE):
    subnet_id = subnet_model.Subnet.insert(**{
        'id': subnet_id,
        'project_id': project_id,
        'network_id': network_id,
        'op_subnet_id': utils.generate_uuid(),
        'name': 'sbnt-name',
        'description': '',
        'gateway_ip': '',
        'ip_start': ip_start,
        'ip_end': ip_end,
        'cidr': cidr,
        'status': status,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })

    return subnet_id


def insert_instance(project_id=project_id_a,
                    instance_id=instance_id_a,
                    name=None,
                    op_server_id=None,
                    op_volume_id=None,
                    network_id=network_id_a,
                    subnet_id=subnet_id_a,
                    image_id=image_id_a,
                    status=instance_model.INSTANCE_STATUS_PENDING):

    instance_id = instance_model.Instance.insert(**{
        'id': instance_id,
        'project_id': project_id,
        'name': name or 'inst-name',
        'description': '',
        'instance_type_id': instance_type_id_a,
        'image_id': image_id,
        'current_vcpus': 1,
        'current_memory': 1024,
        'current_disk': 20,
        'op_server_id': op_server_id or utils.generate_uuid(),
        'op_volume_id': op_volume_id or utils.generate_uuid(),
        'address': '',
        'op_network_id': utils.generate_uuid(),
        'op_subnet_id': utils.generate_uuid(),
        'op_port_id': utils.generate_uuid(),
        'network_id': network_id,
        'subnet_id': subnet_id,
        'status': status,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return instance_id


def insert_instance_volume(project_id=project_id_a,
                           volume_id=volume_id_a,
                           instance_id=instance_id_a):
    instance_volume_model.InstanceVolume.insert(**{
        'id': utils.generate_key(8),
        'instance_id': instance_id,
        'volume_id': volume_id,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow()
    })


def insert_volume(project_id=project_id_a,
                  volume_id=volume_id_a,
                  status=volume_model.VOLUME_STATUS_ACTIVE):
    volume_id = volume_model.Volume.insert(**{
        'id': volume_id,
        'project_id': project_id,
        'status': status,
        'op_volume_id': utils.generate_uuid(),
        'name': 'a_vol',
        'description': 'vol_desc',
        'size': 1,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
        'volume_type': 'sata',
    })
    return volume_id


def insert_project(project_id,
                   qt_instances=2222, qt_vcpus=2222, qt_memory=22220,
                   qt_images=2222, qt_eips=2222, qt_networks=2222,
                   qt_volumes=2222, qt_volume_size=2222, qt_snapshots=2222,
                   qt_key_pairs=2222):
    project_id = project_model.Project.insert(**{
        'id': project_id,
        'op_project_id': utils.generate_key(32),
        'qt_instances': qt_instances,
        'qt_vcpus': qt_vcpus,
        'qt_memory': qt_memory,
        'qt_images': qt_images,
        'qt_eips': qt_eips,
        'qt_networks': qt_networks,
        'qt_volumes': qt_volumes,
        'qt_volume_size': qt_volume_size,
        'qt_snapshots': qt_snapshots,
        'qt_key_pairs': qt_key_pairs,
        'cu_instances': 0,
        'cu_vcpus': 0,
        'cu_memory': 0,
        'cu_images': 0,
        'cu_eips': 0,
        'cu_networks': 0,
        'cu_volumes': 0,
        'cu_volume_size': 0,
        'cu_snapshots': 0,
        'cu_key_pairs': 0,
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return project_id


def insert_job(project_id=project_id_a,
               job_id=job_id_a,
               action=action_a,
               params=params_a,
               status=job_model.JOB_STATUS_PENDING):

    job_id = job_model.Job.insert(**{
        'id': job_id,
        'project_id': project_id,
        'action': action,
        'status': status,
        'error': '',
        'result': '',
        'params': json.dumps(params),
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
        'run_at': datetime.datetime.utcnow(),
        'try_period': 1,
        'try_max': 3,
        'trys': 0,
    })
    return job_id


def insert_operation(action='insert_operation',
                     project_id=project_id_a):

    operation_id = operation_model.Operation.insert(**{
        'id': 'opertn-' + utils.generate_key(10),
        'project_id': project_id,
        'action': action,
        'access_key': 'access_key',
        'params': json.dumps({}),
        'resource_type': 'instance',
        'resource_ids': json.dumps([]),
        'ret_code': 0,
        'ret_message': 'ret_message',
        'updated': datetime.datetime.utcnow(),
        'created': datetime.datetime.utcnow(),
    })
    return operation_id


public = create_api('public').route(
    public_switch).service.service.test_client()
manage = create_api('manage').route(
    manage_switch).service.service.test_client()
worker = create_worker(pick_size=10, exec_size=10, exec_timeout=600)

op_image_example = {
    'name': u'cirros-0.3.4-x86_64-uec-kernel',
    'description': u'',
    'min_disk': 0,
    'min_memory': 0,
    'owner': u'ca187564e43149af8262c88545bdfcf3',
    'protected': False,
    'schema': u'/v2/schemas/image',
    'size': 43164421120,
    'checksum': u'8a40c862b5735975d82605c1dd395796',
    'container_format': u'aki',
    'disk_format': u'aki',
    'file': u'/v2/images/7d61be1a-6769-4355-9d5b-107f83b5dc6e/file',
    'status': u'active',
    'tags': [],
    'created_at': u'2021-06-22T09:14:52Z',
    'updated_at': u'2021-06-23T09:00:59Z',
    'virtual_size': None,
}

op_hypervisor_example = {
    'hypervisor_hostname': 'hyper-name',
    'current_workload': 3,
    'disk_available_least': 20,
    'free_disk_gb': 10,
    'free_ram_mb': 1024,
    'host_ip': '192.168.1.2',
    'hypervisor_type': 'kvm',
    'hypervisor_version': '2.0.0',
    'local_gb': 600,
    'local_gb_used': 500,
    'memory_mb': 10240,
    'memory_mb_used': 1024,
    'running_vms': 9,
    'state': 'up',
    'status': 'enabled',
    'vcpus': 60,
    'vcpus_used': 50,
}

op_mock_server = {
    'id': u'de45d96f-c98a-4a23-a50f-a6b4283cf176',
    'status': u'ACTIVE',
    'updated': u'2021-05-21T13:47:29Z',
    'user_id': u'998845165be64afa80014af00ef1d1d0',
    'project_id': u'253323a788734e3686d7fdc87dc8ca71',
    'metadata': {},
    'name': u'icebox-test',
    'hostId': u'ca48065b1c85d78ee66605ab9fe5dd78ea800197262ab49b8232370c',
    'addresses': {
        u'icebox-tbbuPS2dTr2YroJVMtZhnG': [{
            u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:ae:2f:26',
            u'OS-EXT-IPS:type': u'fixed',
            u'addr': u'192.168.0.3',
            u'version': 4
        }]
    },
    'config_drive': True,
    'flavor': {u'id': u'c3432264-96fe-42e2-8165-343cd92dc67d'},
    'image': {u'id': u'2a0a8fa9-53dd-4ce1-baf1-cebcd25991af'},
    'power_state': 1,
    'task_state': None,
    'vm_state': u'active',
    'OS-EXT-STS:power_state': 1,
    'OS-EXT-STS:task_state': None,
    'OS-EXT-STS:vm_state': u'active',
    'OS-EXT-SRV-ATTR:host': 'compute-108-46.cn-test-1.ecs.i-azure.com',
}

op_mock_image = {
    'id': u'7d61be1a-6769-4355-9d5b-107f83b5dc6e',
    'name': u'cirros-0.3.4-x86_64-uec-kernel',
    'min_disk': 0,
    'min_memory': 0,
    'owner': u'ca187564e43149af8262c88545bdfcf3',
    'protected': False,
    'size': 4979632,
    'checksum': u'8a40c862b5735975d82605c1dd395796',
    'container_format': u'aki',
    'disk_format': u'aki',
    'file': u'/v2/images/7d61be1a-6769-4355-9d5b-107f83b5dc6e/file',
    'status': u'active',
    'tags': [],
    'created': u'2021-06-22T09:14:52Z',
    'updated': u'2021-06-23T09:00:59Z',
    'virtual_size': None,
    'capshot_id': None,
    'block_device_mapping': [],
    'locations': [],
}

op_mock_capshot = {
    'id': '7d61be1a-6769-4355-9d5b-107f83b5dc6e',
    'name': 'a-cap-shot',
    'description': 'capshot desc',
    'volume_id': '0e680a2b-b6e0-40c1-af77-19c635a5fb55',
    'snapshot_id': 'cded633a-9e77-4b20-b8fd-80c937bd3518',
    'provider_location': 'rbd://fsid/poolid/image/snap',
    'size': 1,
    'status': 'creating',
    'updated': '2021-06-22T09:14:52Z',
    'created': '2021-06-22T09:14:52Z',
}

op_mock_port = {
    u'admin_state_up': True,
    u'allowed_address_pairs': [],
    u'binding:host_id': u'm-13-90-test02-yz.bj-cn.vps.azure.com',
    u'binding:profile': {},
    u'binding:vif_details': {u'ovs_hybrid_plug': False, u'port_filter': True},
    u'binding:vif_type': u'ovs',
    u'binding:vnic_type': u'normal',
    u'created_at': u'2021-08-02T02:04:30',
    u'description': u'',
    u'device_id': u'8dcfbd56-039e-4799-bb6a-21c0beb32b26',
    u'device_owner': u'network:router_ha_interface',
    u'dns_name': None,
    u'extra_dhcp_opts': [],
    u'fixed_ips': [{u'ip_address': u'172.16.0.4', u'subnet_id': u'3ea25f47-40b4-439d-8d70-31cff190d3c0'}],  # noqa
    u'id': u'ffffbd09-dcab-4bd1-862a-34568f91a42b',
    u'mac_address': u'fa:16:3f:59:a5:83',
    u'name': u'HA port tenant dd05a04bc8c04b8ba940c237e229ceb3',
    u'network_id': u'f57a338f-6903-4c69-8f1f-e988fa3a7d12',
    u'security_groups': [],
    u'status': u'ACTIVE',
    u'tenant_id': u'',
    u'updated_at': u'2021-08-02T05:28:40'
}

op_mock_volume = {
    'attachments': [],
    'availability_zone': 'nova',
    'bootable': 'false',
    'consistencygroup_id': None,
    'created_at': '2021-05-30T09:41:42.638924',
    'description': None,
    'encrypted': False,
    'id': '0e680a2b-b6e0-40c1-af77-19c635a5fb55',
    'links': [{
        'href': 'http://some.url.href.com',
        'rel': 'self'
    }, {
        'href': 'http://some.url.href.com',
        'rel': 'bookmark'
    }],
    'metadata': {},
    'migration_status': None,
    'multiattach': False,
    'name': 'icebox-thatvol',
    'replication_status': 'disabled',
    'size': 1,
    'snapshot_id': None,
    'source_volid': None,
    'status': 'creating',
    'updated_at': None,
    'user_id': '1884b027b5a34d48b0e2313d613c9ac7',
    'volume_type': 'sata',
    'os-vol-host-attr:host': 'compute-108-15.cn-test-1.ecs.i-azure.com@pool-1#sata',  # noqa
}

op_mock_key_pair = {
    'name': 'icebox-random_!@!#',
    'public_key': '*' * 500,
    'private_key': '*' * 500,
    'fingerprint': '!@#!@#!'
}

op_mock_snapshot = {
    u'id': u'cded633a-9e77-4b20-b8fd-80c937bd3518',
    u'created_at': u'2021-06-22T10:08:08.356268',
    u'description': None,
    u'metadata': {},
    u'name': 'icebox-snapshot-a',
    u'size': 1,
    u'status': u'creating',
    u'updated_at': None,
    u'volume_id': u'4f483541-a048-44ec-93d5-9108480852cd'
}

op_mock_subnet = {
    'subnet': {
        'allocation_pools': [{'end': '192.168.0.254', 'start': '192.168.0.2'}],
        'cidr': '192.168.0.0/24',
        'created_at': '2021-05-20T03:56:51',
        'description': '',
        'dns_nameservers': [],
        'enable_dhcp': True,
        'gateway_ip': '192.168.0.1',
        'host_routes': [],
        'id': utils.generate_uuid(),
        'ip_version': 4,
        'ipv6_address_mode': None,
        'ipv6_ra_mode': None,
        'name': 'icebox-Hh5fCxev7F2nHXfVBPASV8',
        'network_id': utils.generate_uuid(),
        'subnetpool_id': None,
        'tenant_id': 't-s8DwDp34PR',
        'updated_at': '2021-05-20T03:56:51'
    }
}

op_mock_flavor = {
    'name': 'icebox-c12m16d20',
    'is_public': True,
    'ram': 16,
    'disk': 20,
    'rxtx_factor': 1.0,
    'swap': u'',
    'vcpus': 12
}

op_mock_list_ports = {
    'ports': []
}

op_mock_list_networks = {
    'networks': [{
        'admin_state_up': True,
        'availability_zone_hints': [],
        'availability_zones': [],
        'created_at': u'2021-07-29T02:58:23',
        'description': u'',
        'id': u'1dcd0d65-8e75-44f5-8b0d-db69296fa50f',
        'ipv4_address_scope': None,
        'ipv6_address_scope': None,
        'mtu': 1500,
        'name': u'icebox-yz_vlan_wai',
        'provider:network_type': u'vlan',
        'provider:physical_network': u'physnet1',
        'provider:segmentation_id': 10,
        'router:external': True,
        'shared': False,
        'status': u'ACTIVE',
        'subnets': [u'd0fb5bcb-aed9-4d70-bf1a-92df1dfab34b'],
        'tags': [],
        'tenant_id': u'dcad0a17bcb34f969aaf9acba243b4e1',
        'updated_at': u'2021-07-29T03:03:54'
    }]
}

op_mock_list_routers = {
    'routers': [{
        'admin_state_up': True,
        'availability_zone_hints': [],
        'availability_zones': ['nova'],
        'description': '',
        'distributed': False,
        'external_gateway_info': None,
        'ha': True,
        'id': 'f26cfe3b-0c63-4f25-8cbe-13769eaca96c',
        'name': 'icebox-AbXgpWM3caDJmX56tXATVZ',
        'portforwardings': [],
        'routes': [],
        'status': 'ACTIVE',
        'tenant_id': 'dd05a04bc8c04b8ba940c237e229ceb3'
    }],
}

op_mock_add_gateway_router = {
    'router': {
        'admin_state_up': True,
        'availability_zone_hints': [],
        'availability_zones': [u'nova'],
        'description': u'',
        'distributed': False,
        'external_gateway_info': {
            'enable_snat': True,
            'external_fixed_ips': [{
                'ip_address': '10.130.33.130',
                'subnet_id': '20a71625-ed7e-4425-8946-45df0322045e'
            }],
            'network_id': 'f1e4ef9d-fad5-4ca2-86c3-ed189b106b2d'},
        'ha': False,
        'id': '19d01ab1-1687-479c-93ec-afe6a990fc84',
        'name': 'icebox-router1',
        'portforwardings': [],
        'routes': [],
        'status': 'ACTIVE',
        'tenant_id': '1b6b1d44ca374ed3976c042362d73d81'
    },
}

op_mock_remove_gateway_router = {
    'router': {
        'admin_state_up': True,
        'availability_zone_hints': [],
        'availability_zones': [],
        'description': '',
        'distributed': False,
        'external_gateway_info': None,
        'ha': False,
        'id': 'cf576a29-1312-40df-b63a-175e524ade45',
        'name': 'icebox-c8GnbpKBqYTFnNyuiRKLKE',
        'portforwardings': [],
        'routes': [],
        'status': 'ACTIVE',
        'tenant_id': '7c8bac8e812a4013b242f8837d0f97dc'
    },
}

op_mock_create_router = {
    'router': {
        'admin_state_up': True,
        'availability_zone_hints': [],
        'availability_zones': [],
        'description': '',
        'distributed': False,
        'external_gateway_info': None,
        'ha': False,
        'id': 'e75676f0-dfec-4d1e-a11c-0b6ff9e8c639',
        'name': 'icebox-GbSK7BTsGXKhvUUQnJnkxH',
        'portforwardings': [],
        'routes': [],
        'status': 'ACTIVE',
        'tenant_id': 't-s8DwDp34PR'
    }
}

op_mock_create_network = {
    'network': {
        'admin_state_up': True,
        'availability_zone_hints': [],
        'availability_zones': [],
        'created_at': u'2021-07-29T02:58:23',
        'description': u'',
        'id': u'1dcd0d65-8e75-44f5-8b0d-db69296fa50f',
        'ipv4_address_scope': None,
        'ipv6_address_scope': None,
        'mtu': 1500,
        'name': u'icebox-yz_vlan_wai',
        'provider:network_type': u'vlan',
        'provider:physical_network': u'physnet1',
        'provider:segmentation_id': 10,
        'router:external': True,
        'shared': False,
        'status': u'ACTIVE',
        'subnets': [u'd0fb5bcb-aed9-4d70-bf1a-92df1dfab34b'],
        'tags': [],
        'tenant_id': u'dcad0a17bcb34f969aaf9acba243b4e1',
        'updated_at': u'2021-07-29T03:03:54'
    }
}

op_mock_create_floatingip = {
    'floatingip': {
        'description': '',
        'dns_domain': '',
        'fixed_ip_address': None,
        'floating_ip_address': '10.130.33.136',
        'floating_network_id': 'f1e4ef9d-fad5-4ca2-86c3-ed189b106b2d',
        'id': 'a366697b-3839-416f-b568-1608b14281cd',
        'port_id': None,
        'router_id': None,
        'status': 'DOWN',
        'tenant_id': '7c8bac8e812a4013b242f8837d0f97dc'}
}

op_mock_create_loadbalancer = {
    'loadbalancer': {
        'admin_state_up': True,
        'description': '',
        'id': '56f0937b-ccbd-4a99-b02b-1e37b409ba03',
        'listeners': [{'id': 'ac966af2-3d12-4697-889c-5b70027a8e51'}],
        'name': 'test_b',
        'operating_status': 'ONLINE',
        'provider': 'lvs',
        'provisioning_status': 'ACTIVE',
        'tenant_id': '254686300d8f49438fb105b693034181',
        'vip_address': '192.168.1.12',
        'vip_port_id': 'b83e9fc9-3a01-4623-927e-6e0dd8035501'
    }
}

op_mock_create_loadbalancer_member = {
    'member': {
        'address': '10.0.0.3',
        'admin_state_up': True,
        'id': '8a6adc34-38c8-4e99-9ce3-6465500c8559',
        'name': 'b1',
        'protocol_port': 22,
        'subnet_id': 'be36f320-6a31-4aa5-96a3-baf082da6305',
        'tenant_id': '254686300d8f49438fb105b693034181',
        'weight': 1
    }
}

op_mock_create_loadbalancer_listener = {
    'listener': {
        'admin_state_up': True,
        'connection_limit': -1,
        'default_pool_id': None,
        'default_tls_container_ref': None,
        'description': '',
        'id': '94e2348e-91c4-45e5-b38c-9a321f13e464',
        'loadbalancers': [{'id': 'ce162f4d-89da-471c-91bd-136146097dcb'}],
        'name': 'l1',
        'protocol': 'TCP',
        'protocol_port': 80,
        'sni_container_refs': [],
        'tenant_id': '254686300d8f49438fb105b693034181'
    }
}

op_mock_create_loadbalancer_pool = {
    'pool': {
        'admin_state_up': True,
        'description': '',
        'healthmonitor_id': None,
        'id': 'a5d74f07-0071-4095-a59c-a4dda2975f06',
        'lb_algorithm': 'ROUND_ROBIN',
        'listeners': [{'id': '94e2348e-91c4-45e5-b38c-9a321f13e464'}],
        'members': [],
        'name': 'p1',
        'protocol': 'TCP',
        'session_persistence': None,
        'tenant_id': '254686300d8f49438fb105b693034181'
    }
}

op_mock_create_loadbalancer_healthmonitor = {
    'healthmonitor': {
        'admin_state_up': True,
        'delay': 10,
        'id': '81633c1c-d83d-480d-9709-466eaffe3cc5',
        'max_retries': 3,
        'name': '',
        'pools': [{'id': 'a5d74f07-0071-4095-a59c-a4dda2975f06'}],
        'tenant_id': '254686300d8f49438fb105b693034181',
        'timeout': 10,
        'type': 'TCP'
    }
}

op_mock_project = {
    'enabled': True,
    'description': 'a demo project',
    'name': 'icebox-demo-project',
}

op_mock_role = {
    'domain_id': None,
    'name': 'admin',
    'id': '1ddfe1a8e2ca47e2bbd0d080a7fb037f'
}

op_mock_user = {
    'username': 'admin',
    'enabled': True,
    'name': 'admin',
    'id': 'c71ec5303b174121a96f4a90404a5e9b'
}

op_mock_update_quota = {
    'quota': {
        'floatingip': 1000,
        'network': 1000,
        'port': 1000,
        'rbac_policy': 10,
        'router': 1000,
        'security_group': 10,
        'security_group_rule': 10,
        'subnet': 1000,
        'subnetpool': 2000
    }
}

op_mock_get_monitor = []
