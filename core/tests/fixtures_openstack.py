from densefog.common import utils

#################################################################
#
# raw objects returned directly from openstack components,
# such as compute, block, network, image.
#
#################################################################


op_mock_hypervisor = {
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

op_mock_list_statistics = []

op_mock_server = {
    'id': u'de45d96f-c98a-4a23-a50f-a6b4283cf176',
    'status': u'ACTIVE',
    'updated': u'2021-05-21T13:47:29Z',
    'user_id': u'998845165be64afa80014af00ef1d1d0',
    'tenant_id': u'253323a788734e3686d7fdc87dc8ca71',
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
    'OS-EXT-STS:power_state': 1,
    'OS-EXT-STS:task_state': None,
    'OS-EXT-STS:vm_state': u'active',
    'OS-EXT-SRV-ATTR:host': 'compute-108-46.cn-test-1.ecs.i-azure.com',
}

op_mock_image = {
    'id': u'7d61be1a-6769-4355-9d5b-107f83b5dc6e',
    'name': u'cirros-0.3.4-x86_64-uec-kernel',
    'min_disk': 0,
    'min_ram': 0,
    'owner': u'ca187564e43149af8262c88545bdfcf3',
    'protected': False,
    'size': 4979632,
    'checksum': u'8a40c862b5735975d82605c1dd395796',
    'container_format': u'aki',
    'disk_format': u'aki',
    'file': u'/v2/images/7d61be1a-6769-4355-9d5b-107f83b5dc6e/file',
    'status': u'active',
    'tags': [],
    'created_at': u'2021-06-22T09:14:52Z',
    'updated_at': u'2021-06-23T09:00:59Z',
    'virtual_size': None,
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
    u'port': {
        u'admin_state_up': True,
        u'allowed_address_pairs': [],
        u'binding:host_id': u'm-13-90-test02-yz.bj-cn.vps.azure.com',
        u'binding:profile': {},
        u'binding:vif_details': {u'ovs_hybrid_plug': False, u'port_filter': True},  # noqa
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
}

op_mock_port_forwarding = {
    u'id': u'84d897ef-8c5e-4583-b911-ab38ea9e1381',
    u'inside_addr': u'192.168.200.110',
    u'inside_port': 22,
    u'outside_port': 2222,
    u'protocol': u'tcp',
    u'router_id': u'8074db79-53d5-4b27-bb5b-8a76bf2b1f23'
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

op_mock_list_subnets = {
    'subnets': [{
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
    }]
}

op_mock_floatingip = {
    'floatingip': {
        u'description': u'icebox-floatingip',
        u'dns_domain': u'',
        u'dns_name': u'',
        u'fixed_ip_address': u'192.168.200.4',
        u'floating_ip_address': u'10.248.1.229',
        u'floating_network_id': u'96979733-4023-4a65-8033-a51461fe89c6',
        u'id': u'2093951a-f25d-45fc-9e8f-b48c8869a7d1',
        u'name': u'',
        u'port_id': u'f58c1038-7f89-497f-a918-99aa4f9ed32c',
        u'rate_limit': 1,
        u'router_id': u'f58545b4-095b-4d2d-a6dd-824edb8fb6fd',
        u'status': u'ACTIVE',
        u'tenant_id': u'74db94df23ad458587ec55f3fcc5b4f9'
    }
}

op_mock_list_floatingips = {
    'floatingips': [{
        u'description': u'icebox-floatingip',
        u'dns_domain': u'',
        u'dns_name': u'',
        u'fixed_ip_address': u'192.168.200.4',
        u'floating_ip_address': u'10.248.1.229',
        u'floating_network_id': u'96979733-4023-4a65-8033-a51461fe89c6',
        u'id': u'2093951a-f25d-45fc-9e8f-b48c8869a7d1',
        u'name': u'',
        u'port_id': u'f58c1038-7f89-497f-a918-99aa4f9ed32c',
        u'rate_limit': 1,
        u'router_id': u'f58545b4-095b-4d2d-a6dd-824edb8fb6fd',
        u'status': u'ACTIVE',
        u'tenant_id': u'74db94df23ad458587ec55f3fcc5b4f9'
    }]
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
    'ports': [{
        u'admin_state_up': True,
        u'allowed_address_pairs': [],
        u'binding:host_id': u'm-13-90-test02-yz.bj-cn.vps.azure.com',
        u'binding:profile': {},
        u'binding:vif_details': {u'ovs_hybrid_plug': False, u'port_filter': True},  # noqa
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
    }]
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

op_mock_get_router = {
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

op_mock_get_network = {
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
