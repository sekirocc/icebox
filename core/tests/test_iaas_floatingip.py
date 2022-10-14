import env  # noqa
import patches
from mock import patch
from nose import tools
from icebox.model.iaas import floatingip as fip_model
# from icebox.model.iaas import error as iaas_error

import fixtures


def mock_public_network(*args, **kwargs):
    """
    there are one public network
    """
    return {
        u'admin_state_up': True,
        u'availability_zone_hints': [],
        u'availability_zones': [],
        u'created_at': u'2021-09-09T10:29:18',
        u'description': u'',
        u'id': u'd3a53127-ce1c-4271-8d57-e1f8874c2986',
        u'ipv4_address_scope': None,
        u'ipv6_address_scope': None,
        u'is_default': False,
        u'mtu': 1500,
        u'name': u'wai',
        u'port_security_enabled': True,
        u'provider:network_type': u'flat',
        u'provider:physical_network': u'external',
        u'provider:segmentation_id': None,
        u'router:external': True,
        u'shared': False,
        u'status': u'ACTIVE',
        u'subnets': [u'ddb7fa20-274e-47e1-94ee-898fe1bf8e14'],
        u'tags': [],
        u'tenant_id': u'dcad0a17bcb34f969aaf9acba243b4e1',
        u'updated_at': u'2021-09-09T10:29:18'
    }


def mock_list_subnets(*args, **kwargs):
    """
    the public network has one subnet.
        10.148.200.2 => 10.148.200.254
    """
    return {
        'subnets': [{
            u'allocation_pools':
                [{u'end': u'10.148.200.254', u'start': u'10.148.200.2'}],
            u'cidr': u'10.148.200.0/24',
            u'created_at': u'2021-09-09T10:30:24',
            u'description': u'',
            u'dns_nameservers': [],
            u'enable_dhcp': False,
            u'gateway_ip': u'10.148.200.1',
            u'host_routes': [],
            u'id': u'ddb7fa20-274e-47e1-94ee-898fe1bf8e14',
            u'ip_version': 4,
            u'ipv6_address_mode': None,
            u'ipv6_ra_mode': None,
            u'name': u'wai_1',
            u'network_id': u'd3a53127-ce1c-4271-8d57-e1f8874c2986',
            u'subnetpool_id': None,
            u'tenant_id': u'dcad0a17bcb34f969aaf9acba243b4e1',
            u'updated_at': u'2021-09-09T10:30:24'
        }]
    }['subnets']


def mock_list_routers(*args, **kwargs):
    """
    used ips:
        10.148.200.231
        10.148.200.40
        10.148.200.225
    """
    return {
        'routers': [{
            u'admin_state_up': True,
            u'availability_zone_hints': [],
            u'availability_zones': [u'az1'],
            u'description': u'',
            u'distributed': False,
            u'external_gateway_info': {
                u'enable_snat': True,
                u'external_fixed_ips': [{
                    u'ip_address': u'10.148.200.231',
                    u'subnet_id': u'ddb7fa20-274e-47e1-94ee-898fe1bf8e14'
                }],
                u'network_id': u'd3a53127-ce1c-4271-8d57-e1f8874c2986',
                u'rate_limit': 119
            },
            u'ha': True,
            u'id': u'004e0916-7ca6-49c9-a0f3-0aefa68f85cf',
            u'name': u'icebox-rutr-keYYUnQX',
            u'portforwardings': [],
            u'routes': [],
            u'status': u'ACTIVE',
            u'tenant_id': u'f65e8d2b01b9405b8380e0652da9f851'
        }, {
            u'admin_state_up': True,
            u'availability_zone_hints': [],
            u'availability_zones': [u'az1'],
            u'description': u'',
            u'distributed': False,
            u'external_gateway_info': None,
            u'ha': True,
            u'id': u'05c82799-e7d4-4dac-be0f-9f6d7ae68179',
            u'name': u'icebox-rutr-t9x2AUim',
            u'portforwardings': [],
            u'routes': [],
            u'status': u'ACTIVE',
            u'tenant_id': u'307e156d26e84c9ca40b8b30b5b788c1'
        }, {
            u'admin_state_up': True,
            u'availability_zone_hints': [],
            u'availability_zones': [u'az1'],
            u'description': u'',
            u'distributed': False,
            u'external_gateway_info': {
                u'enable_snat': True,
                u'external_fixed_ips': [{
                    u'ip_address': u'10.148.200.40',
                    u'subnet_id': u'ddb7fa20-274e-47e1-94ee-898fe1bf8e14'
                }],
                u'network_id': u'd3a53127-ce1c-4271-8d57-e1f8874c2986',
                u'rate_limit': 1
            },
            u'ha': True,
            u'id': u'17c64498-1413-4143-8c68-51194ed3add2',
            u'name': u'icebox-rutr-ugrpvLmS',
            u'portforwardings': [],
            u'routes': [],
            u'status': u'ACTIVE',
            u'tenant_id': u'6133ffa8428e4af783cbf5870bb88361'
        }, {
            u'admin_state_up': True,
            u'availability_zone_hints': [],
            u'availability_zones': [u'az1'],
            u'description': u'',
            u'distributed': False,
            u'external_gateway_info': {
                u'enable_snat': True,
                u'external_fixed_ips': [{
                    u'ip_address': u'10.148.200.225',
                    u'subnet_id': u'ddb7fa20-274e-47e1-94ee-898fe1bf8e14'
                }],
                u'network_id': u'd3a53127-ce1c-4271-8d57-e1f8874c2986',
                u'rate_limit': 1
            },
            u'ha': True,
            u'id': u'fc95f9da-0dc1-4aa1-bb41-dae5fdbcb5cd',
            u'name': u'icebox-rutr-FUWNEvYY',
            u'portforwardings': [],
            u'routes': [],
            u'status': u'ACTIVE',
            u'tenant_id': u'e96ef8eaf993409686d823efd288d866'
        }]
    }['routers']


def mock_list_floatingips(*args, **kwargs):
    """
    eip used
        10.148.200.145
        10.148.200.127
        10.148.200.9
    """
    return {
        'floatingips': [{
            u'description': u'icebox-floatingip',
            u'dns_domain': u'',
            u'dns_name': u'',
            u'fixed_ip_address': None,
            u'floating_ip_address': u'10.148.200.145',
            u'floating_network_id': u'd3a53127-ce1c-4271-8d57-e1f8874c2986',
            u'id': u'046cda92-f1a3-46fb-8676-4e721300e420',
            u'name': u'',
            u'port_id': None,
            u'rate_limit': 1,
            u'router_id': None,
            u'status': u'DOWN',
            u'tenant_id': u'307e156d26e84c9ca40b8b30b5b788c1'
        }, {
            u'description': u'icebox-floatingip',
            u'dns_domain': u'',
            u'dns_name': u'',
            u'fixed_ip_address': u'192.164.0.5',
            u'floating_ip_address': u'10.148.200.127',
            u'floating_network_id': u'd3a53127-ce1c-4271-8d57-e1f8874c2986',
            u'id': u'2c2f9fb3-af88-43ee-830c-f9a72f70ab3a',
            u'name': u'',
            u'port_id': u'94c02e55-8eef-4bb7-b479-635de31f570d',
            u'rate_limit': 300,
            u'router_id': u'004e0916-7ca6-49c9-a0f3-0aefa68f85cf',
            u'status': u'ACTIVE',
            u'tenant_id': u'f65e8d2b01b9405b8380e0652da9f851'
        }, {
            u'description': u'icebox-floatingip',
            u'dns_domain': u'',
            u'dns_name': u'',
            u'fixed_ip_address': u'192.168.0.2',
            u'floating_ip_address': u'10.148.200.9',
            u'floating_network_id': u'd3a53127-ce1c-4271-8d57-e1f8874c2986',
            u'id': u'fcdc9ae3-cefc-4920-9cd5-b8d809789bf8',
            u'name': u'',
            u'port_id': u'9c6aa060-e4bb-4372-9b10-d98b945605ca',
            u'rate_limit': 1,
            u'router_id': u'71d26eae-34e8-4e4f-a36e-bdc042f77f79',
            u'status': u'ACTIVE',
            u'tenant_id': u'f65e8d2b01b9405b8380e0652da9f851'
        }]
    }['floatingips']


@patches.nova_authenticate
class TestModel:

    def setup(self):
        env.reset_db()

    def test_create_ips(self):
        fip_model.create_ips(ips=['192.168.200.1', '192.168.200.2'])
        fip_model.release_ips(ips=['192.168.200.1'])

        tools.eq_(fip_model.limitation()['total'], 2)

    def test_release_ips(self):
        fixtures.insert_floatingip('fip-a', '192.168.200.1')
        fixtures.insert_floatingip('fip-b', '192.168.200.2')
        fixtures.insert_floatingip('fip-c', '192.168.200.3', status=fip_model.FLOATINGIP_STATUS_DELETED)  # noqa

        tools.eq_(fip_model.limitation(status=fip_model.FLOATINGIP_STATUS_ACTIVE)['total'], 2)  # noqa

        fip_model.release_ips(ips=['192.168.200.3'])
        tools.eq_(fip_model.limitation(status=fip_model.FLOATINGIP_STATUS_ACTIVE)['total'], 3)  # noqa

    def test_consume_ips(self):
        fixtures.insert_floatingip('fip-a', '192.168.200.1')
        fixtures.insert_floatingip('fip-b', '192.168.200.2')
        fixtures.insert_floatingip('fip-c', '192.168.200.3', status=fip_model.FLOATINGIP_STATUS_DELETED)  # noqa

        tools.eq_(fip_model.limitation(status=fip_model.FLOATINGIP_STATUS_ACTIVE)['total'], 2)  # noqa

        fip_model.consume_ips(ips=['192.168.200.2'])
        tools.eq_(fip_model.limitation(status=fip_model.FLOATINGIP_STATUS_ACTIVE)['total'], 1)  # noqa

    def test_count(self):
        fixtures.insert_floatingip('fip-a', '192.168.200.1')
        fixtures.insert_floatingip('fip-b', '192.168.200.2')
        fixtures.insert_floatingip('fip-c', '192.168.200.3', status=fip_model.FLOATINGIP_STATUS_DELETED)  # noqa

        tools.eq_(fip_model.count(status=fip_model.FLOATINGIP_STATUS_ACTIVE), 2)  # noqa
        tools.eq_(fip_model.count(status=fip_model.FLOATINGIP_STATUS_DELETED), 1)  # noqa

    def test_limitation(self):
        fixtures.insert_floatingip('fip-a', '192.168.200.1')
        fixtures.insert_floatingip('fip-b', '192.168.200.2')
        fixtures.insert_floatingip('fip-c', '192.168.200.3', status=fip_model.FLOATINGIP_STATUS_DELETED)  # noqa

        page = fip_model.limitation(status=fip_model.FLOATINGIP_STATUS_ACTIVE)
        tools.eq_(len(page['items']), 2)

        ips = [fip['address'] for fip in page['items']]
        tools.ok_('192.168.200.1' in ips)
        tools.ok_('192.168.200.2' in ips)

        page = fip_model.limitation(status=fip_model.FLOATINGIP_STATUS_DELETED)
        tools.eq_(len(page['items']), 1)

        ips = [fip['address'] for fip in page['items']]
        tools.ok_('192.168.200.3' in ips)

    @patch('icebox.model.iaas.openstack.api.do_get_public_network', mock_public_network)   # noqa
    @patch('icebox.model.iaas.openstack.api.do_list_subnets', mock_list_subnets)           # noqa
    @patch('icebox.model.iaas.openstack.api.do_list_routers', mock_list_routers)           # noqa
    @patch('icebox.model.iaas.openstack.api.do_list_floatingips', mock_list_floatingips)   # noqa
    def test_sync_all(self):
        # this public subnet allocation pools has 253 ips
        #     10.148.200.2 => 10.148.200.254
        # routers used
        #     10.148.200.231
        #     10.148.200.40
        #     10.148.200.225
        # eip used
        #     10.148.200.9
        #     10.148.200.127
        #     10.148.200.145

        # prepare some ips in db
        fixtures.insert_floatingip('fip-a', '10.148.200.9')
        fixtures.insert_floatingip('fip-b', '10.148.200.127')
        fixtures.insert_floatingip('fip-c', '10.148.200.145', status=fip_model.FLOATINGIP_STATUS_DELETED)  # noqa
        fixtures.insert_floatingip('fip-d', '10.148.200.254', status=fip_model.FLOATINGIP_STATUS_DELETED)  # noqa

        fip_model.sync_all()
        # after sync all.
        # 9 and 127 will be deleted (because eip used them)
        # 145 will not change
        # 254 will be activated     (because no routers or eips used it)
        #
        # result: 2 deleted (9, 127, 145)
        #         253 - 3 - 3 = 247 active
        tools.eq_(fip_model.count(status=fip_model.FLOATINGIP_STATUS_DELETED), 3)  # noqa
        tools.eq_(fip_model.count(status=fip_model.FLOATINGIP_STATUS_ACTIVE), 247)  # noqa

        page = fip_model.limitation(status=fip_model.FLOATINGIP_STATUS_DELETED, limit=0)  # noqa
        tools.eq_(page['total'], 3)

        ips = [fip['address'] for fip in page['items']]
        tools.ok_('10.148.200.9' in ips)

        page = fip_model.limitation(status=fip_model.FLOATINGIP_STATUS_ACTIVE, limit=0)  # noqa
        tools.eq_(page['total'], 247)

        ips = [fip['address'] for fip in page['items']]

        tools.ok_('10.148.200.100' in ips)
        tools.ok_('10.148.200.101' in ips)
        tools.ok_('10.148.200.102' in ips)

        tools.ok_('10.148.200.230' in ips)
        tools.ok_('10.148.200.231' not in ips)
        tools.ok_('10.148.200.232' in ips)
