import env  # noqa
import copy
from mock import patch
from mock import MagicMock
from nose import tools
from densefog.common.utils import MockObject
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import volume as volume_model
from icebox.model.iaas import instance_type as instance_type_model
from icebox.model.iaas.openstack import api as op_api

import fixtures
import fixtures_openstack as op_fixtures

project_id_1 = 'projct-1234'
op_project_id = 'dcad0a17bcb34f969aaf9acba243b4e1'
exc = Exception('HTTP Connection Error')


def mock_nope(*args, **kwargs):
    return None


class TestAPI:
    def setup(self):
        env.reset_db()
        instance_type_id = fixtures.insert_instance_type(project_id_1)
        instance_id = fixtures.insert_instance(project_id_1, status='active')

        self.instance = instance_model.get(instance_id)
        self.instance_type = instance_type_model.get(instance_type_id)

        volume_id = fixtures.insert_volume(project_id_1)
        self.volume = volume_model.get(volume_id)

    @patch('cinderclient.v2.volumes.VolumeManager.create')
    def test_do_create_boot_volume(self, volume_create):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_volume))
        mock.bootable = 'true'

        volume_create.side_effect = [mock, exc]

        # first invoke, success
        boot_volume = op_api.do_create_boot_volume(op_project_id,
                                                   'some-op-image-id',
                                                   'coolname')
        tools.eq_(boot_volume['name'], mock.name)
        tools.eq_(boot_volume['status'], mock.status)
        tools.eq_(boot_volume['bootable'], True)

        # second invoke, catched Exception
        with tools.assert_raises(iaas_error.ProviderCreateBootVolumeError):
            op_api.do_create_boot_volume(op_project_id,
                                         'some-op-image-id',
                                         'coolname')

    @patch('cinderclient.v2.volumes.VolumeManager.create')
    def test_do_create_data_volume(self, volume_create):
        volume_name = 'coolname',
        volume_size = 1
        volume_type = 'sata'

        mock = MockObject(**copy.copy(op_fixtures.op_mock_volume))
        mock.name = volume_name
        mock.size = volume_size
        mock.volume_type = volume_type

        volume_create.side_effect = [mock, exc]

        # first invoke, success
        data_volume = op_api.do_create_data_volume(op_project_id,
                                                   volume_size,
                                                   volume_name,
                                                   volume_type,
                                                   None)
        tools.eq_(data_volume['name'], volume_name)
        tools.eq_(data_volume['size'], volume_size)
        tools.eq_(data_volume['volume_type'], volume_type)

        # second invoke, catched Exception
        with tools.assert_raises(iaas_error.ProviderCreateVolumeError):
            op_api.do_create_data_volume(op_project_id,
                                         volume_size,
                                         volume_name,
                                         volume_type,
                                         None)

    @patch('neutronclient.v2_0.client.Client.create_port')
    def test_do_create_port(self, port_create):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_port))

        port_create.side_effect = [mock, exc]

        port = op_api.do_create_port(op_project_id,
                                     'op-net-id',
                                     'op-subnet-id')

        # first invoke, success
        tools.eq_(port['device_id'], mock.port['device_id'])
        tools.eq_(port['device_owner'], mock.port['device_owner'])
        tools.eq_(port['name'], mock.port['name'])
        tools.eq_(port['network_id'], mock.port['network_id'])
        tools.eq_(port['status'], mock.port['status'])

        # second invoke, catched Exception
        with tools.assert_raises(iaas_error.ProviderCreatePortError):
            op_api.do_create_port(op_project_id,
                                  'op-net-id',
                                  'op-subnet-id')

    @patch('novaclient.v2.servers.ServerManager.create')
    def test_do_create_server(self, server_create):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_server))
        server_create.side_effect = [mock, exc]

        # first invoke, success
        server = op_api.do_create_server(op_project_id, 'coolname',
                                         'op-volume-id', 'op-flavor-id',
                                         'op-network-id', 'op-port-id',
                                         'key-pair-id', 'login-password',
                                         'user-data')

        tools.eq_(server['name'], mock.name)
        tools.eq_(server['status'], mock.status)

        # second invoke, catched Exception
        with tools.assert_raises(iaas_error.ProviderCreateServerError):
            op_api.do_create_server(op_project_id, 'coolname',
                                    'op-volume-id', 'op-flavor-id',
                                    'op-network-id', 'op-port-id',
                                    'key-pair-id', 'login-password',
                                    'user-data')

    @patch('neutronclient.v2_0.client.Client.delete_port')
    def test_do_delete_port_with_id(self, port_delete):
        port_delete.side_effect = [None, exc]

        # first invoke, success
        op_api.do_delete_port(None, 'op-port-id')

        # second invoke, catched Exception
        with tools.assert_raises(iaas_error.ProviderDeletePortError):
            op_api.do_delete_port(None, 'op-port-id')

    @patch('neutronclient.v2_0.client.Client.delete_port')
    def test_do_delete_port_with_instance(self, port_delete):
        port_delete.side_effect = [None, exc]

        # first invoke, success
        op_api.do_delete_port(self.instance, None)

        # second invoke, catched Exception
        with tools.assert_raises(iaas_error.ProviderDeletePortError):
            op_api.do_delete_port(self.instance, None)

    @patch('novaclient.v2.servers.ServerManager.interface_detach')
    def test_do_interface_detach(self, detach_interface):
        detach_interface.side_effect = [None, exc]

        op_api.do_interface_detach(self.instance)

        with tools.assert_raises(iaas_error.ProviderInterfaceDetachError):
            op_api.do_interface_detach(self.instance)

    @patch('novaclient.v2.servers.ServerManager.get')
    def test_do_get_server(self, server_get):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_server))
        server_get.side_effect = [mock, exc]

        op_api.do_get_server('op-server-id')

        with tools.assert_raises(iaas_error.ProviderGetServerError):
            op_api.do_get_server('op-server-id')

    @patch('novaclient.v2.servers.ServerManager.stop')
    def test_do_stop_server(self, server_stop):
        server_stop.side_effect = [None, exc]

        op_api.do_stop_server(self.instance)

        with tools.assert_raises(iaas_error.ProviderStopServerError):
            op_api.do_stop_server(self.instance)

    @patch('novaclient.v2.servers.ServerManager.start')
    def test_do_start_server(self, server_start):
        server_start.side_effect = [None, exc]

        op_api.do_start_server(self.instance)

        with tools.assert_raises(iaas_error.ProviderStartServerError):
            op_api.do_start_server(self.instance)

    @patch('novaclient.v2.servers.ServerManager.reboot')
    def test_do_reboot_server(self, server_reboot):
        server_reboot.side_effect = [None, exc]

        op_api.do_reboot_server(self.instance, 'SOFT')

        with tools.assert_raises(iaas_error.ProviderRebootServerError):
            op_api.do_reboot_server(self.instance, 'SOFT')

    @patch('novaclient.v2.servers.ServerManager.resize')
    def test_do_resize_server(self, server_resize):
        server_resize.side_effect = [None, exc]

        op_api.do_resize_server(self.instance, self.instance_type)

        with tools.assert_raises(iaas_error.ProviderResizeServerError):
            op_api.do_resize_server(self.instance, self.instance_type)

    @patch('novaclient.v2.servers.ServerManager.confirm_resize')
    def test_do_confirm_resize_server(self, server_confirm_resize):
        server_confirm_resize.side_effect = [None, exc]

        op_api.do_confirm_resize_server('op-server-id')

        with tools.assert_raises(iaas_error.ProviderConfirmResizeServerError):
            op_api.do_confirm_resize_server('op-server-id')

    def test_do_get_vnc_console(self):
        # donot test this for now.
        pass

    def test_do_get_console_output(self):
        # donot test this for now.
        pass

    @patch('icebox.model.iaas.openstack.compute.change_keypair')
    def test_do_change_keypair(self, server_change_keypair):
        server_change_keypair.side_effect = [None, exc]

        op_api.do_change_keypair(self.instance, 'op-keypair-id')

        with tools.assert_raises(iaas_error.ProviderChangeKeyPairError):
            op_api.do_change_keypair(self.instance, 'op-keypair-id')

    @patch('novaclient.v2.servers.ServerManager.change_password')
    def test_do_change_password(self, server_change_password):
        server_change_password.side_effect = [None, exc]

        op_api.do_change_password(self.instance, 'new-pa33wo4d')

        with tools.assert_raises(iaas_error.ProviderChangePasswordError):
            op_api.do_change_password(self.instance, 'new-pa33wo4d')

    @patch('novaclient.v2.servers.ServerManager.delete')
    def test_do_delete_server_with_id(self, server_delete):
        server_delete.side_effect = [None, exc]
        op_api.do_delete_server(None, 'op-server-id')

        with tools.assert_raises(iaas_error.ProviderDeleteServerError):
            op_api.do_delete_server(None, 'op-server-id')

    @patch('novaclient.v2.servers.ServerManager.delete')
    def test_do_delete_server_with_instance(self, server_delete):
        server_delete.side_effect = [None, exc]
        op_api.do_delete_server(self.instance, 'op-server-id')

        with tools.assert_raises(iaas_error.ProviderDeleteServerError):
            op_api.do_delete_server(self.instance, 'op-server-id')

    @patch('cinderclient.v2.volumes.VolumeManager.delete')
    def test_do_delete_boot_volume(self, volume_delete):
        volume_delete.side_effect = [None, exc]
        op_api.do_delete_boot_volume(self.instance)

        with tools.assert_raises(iaas_error.ProviderDeleteBootVolumeError):
            op_api.do_delete_boot_volume(self.instance)

        pass

    @patch('cinderclient.v2.volumes.VolumeManager.delete')
    def test_do_delete_volume_with_id(self, volume_delete):
        volume_delete.side_effect = [None, exc]
        op_api.do_delete_volume(None, 'op-volume-id')

        with tools.assert_raises(iaas_error.ProviderDeleteVolumeError):
            op_api.do_delete_volume(None, 'op-volume-id')

    @patch('cinderclient.v2.volumes.VolumeManager.delete')
    def test_do_delete_volume_with_volume(self, volume_delete):
        volume_delete.side_effect = [None, exc]
        op_api.do_delete_volume(self.volume, None)

        with tools.assert_raises(iaas_error.ProviderDeleteVolumeError):
            op_api.do_delete_volume(self.volume, None)

    @patch('cinderclient.v2.volumes.VolumeManager.get')
    def test_do_get_volume(self, volume_get):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_volume))
        volume_get.side_effect = [mock, exc]

        op_api.do_get_volume('op-volume-id')

        with tools.assert_raises(iaas_error.ProviderGetVolumeError):
            op_api.do_get_volume('op-volume-id')

    @patch('cinderclient.v2.volumes.VolumeManager.extend')
    def test_do_extend_volume(self, volume_extend):
        volume_extend.side_effect = [None, exc]
        op_api.do_extend_volume(self.volume, 2)

        with tools.assert_raises(iaas_error.ProviderExtendVolumeError):
            op_api.do_extend_volume(self.volume, 2)

    @patch('novaclient.v2.volumes.VolumeManager.create_server_volume')
    def test_do_attach_volume(self, server_volume_create):
        server_volume_create.side_effect = [None, exc]
        op_api.do_attach_volume(self.instance, self.volume)

        with tools.assert_raises(iaas_error.ProviderCreateServerVolumeError):
            op_api.do_attach_volume(self.instance, self.volume)

    @patch('novaclient.v2.volumes.VolumeManager.delete_server_volume')
    def test_do_detach_volume(self, volume_delete_server):
        volume_delete_server.side_effect = [None, exc]
        op_api.do_detach_volume(self.instance, self.volume)

        with tools.assert_raises(iaas_error.ProviderDeleteServerVolumeError):
            op_api.do_detach_volume(self.instance, self.volume)

    @patch('novaclient.v2.servers.ServerManager.create_image')
    @patch('glanceclient.v2.images.Controller.get')
    def test_do_nova_create_image(self, image_get, image_create):
        min_disk = 20
        min_memory = 1024

        mock1 = MockObject(**copy.copy(op_fixtures.op_mock_image))
        image_create.side_effect = [mock1, exc]

        mock2 = MockObject(**copy.copy(op_fixtures.op_mock_image))
        mock2.min_disk = min_disk
        mock2.min_ram = min_memory
        image_get.return_value = mock2

        image = op_api.do_nova_create_image(op_project_id,
                                            'op-server-id',
                                            'coolname')

        tools.eq_(image['min_disk'], min_disk)
        tools.eq_(image['min_memory'], min_memory)

        with tools.assert_raises(iaas_error.ProviderCreateImageError):
            op_api.do_nova_create_image(op_project_id,
                                        'op-server-id',
                                        'coolname')

    @patch('glanceclient.v2.images.Controller.create')
    @patch('glanceclient.v2.images.Controller.add_location')
    @patch('glanceclient.v2.images.Controller.get')
    def test_do_glance_create_image(self, image_get, location_add,
                                    image_create):
        capshot_id = 'op-capshot-id'
        capshot_location = 'rbd://fsid/poolid/image/snap'
        min_disk = 20
        min_memory = 1024

        mock1 = MockObject(**copy.copy(op_fixtures.op_mock_image))
        mock1.capshot_id = capshot_id
        image_create.side_effect = [mock1, exc]

        mock2 = MockObject(**copy.copy(op_fixtures.op_mock_image))
        mock2.locations = [{'url': capshot_location, 'metadata': {}}]
        location_add.return_value = mock2

        mock3 = MockObject(**copy.copy(op_fixtures.op_mock_image))
        mock3.capshot_id = capshot_id
        mock3.locations = [{'url': capshot_location, 'metadata': {}}]
        mock3.min_disk = min_disk
        mock3.min_ram = min_memory
        image_get.return_value = mock3

        image = op_api.do_glance_create_image('op_image_id', 'coolname',
                                              min_disk, min_memory,
                                              capshot_id,
                                              capshot_location)

        tools.eq_(image['locations'][0]['url'], capshot_location)
        tools.eq_(image['capshot_id'], capshot_id)
        tools.eq_(image['min_disk'], min_disk)
        tools.eq_(image['min_memory'], min_memory)

        with tools.assert_raises(iaas_error.ProviderCreateImageError):
            op_api.do_glance_create_image('op_image_id', 'coolname',
                                          min_disk, min_memory,
                                          capshot_id,
                                          capshot_location)

    @patch('glanceclient.v2.images.Controller.list')
    def test_do_list_images(self, image_list):
        mock1 = MockObject(**copy.copy(op_fixtures.op_mock_image))
        mock2 = MockObject(**copy.copy(op_fixtures.op_mock_image))
        image_list.side_effect = [[mock1, mock2], exc]

        op_api.do_list_images()

        with tools.assert_raises(iaas_error.ProviderListImagesError):
            op_api.do_list_images()

    @patch('glanceclient.v2.images.Controller.get')
    def test_do_get_image(self, image_get):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_image))
        image_get.side_effect = [mock, exc]

        op_api.do_get_image('op-image-id')

        with tools.assert_raises(iaas_error.ProviderGetImageError):
            op_api.do_get_image('op-image-id')

    @patch('glanceclient.v2.images.Controller.delete')
    def test_do_delete_image(self, image_delete):
        image_delete.side_effect = [None, exc]
        op_api.do_delete_image('op-image-id')

        with tools.assert_raises(iaas_error.ProviderCreateImageError):
            op_api.do_delete_image('op-image-id')

    def test_do_create_capshot(self):
        # TODO! NOW CLIENT DOES NOT SUPPORT CAPSHOT.

        # params.side_effect = [mock, exc]
        # op_api.do_create_capshot()

        # with tools.assert_raises(iaas_error.ProviderCreateCapshotError):
        #     op_api.do_create_capshot()

        pass

    def test_do_delete_capshot(self):
        # TODO! NOW CLIENT DOES NOT SUPPORT CAPSHOT.

        # params.side_effect = [mock, exc]
        # op_api.do_delete_capshot()

        # with tools.assert_raises(iaas_error.ProviderDeleteCapshotError):
        #     op_api.do_delete_capshot()

        pass

    @patch('cinderclient.v2.volume_snapshots.SnapshotManager.delete')
    def test_do_delete_snapshot(self, snapshot_delete):
        snapshot_delete.side_effect = [None, exc]
        op_api.do_delete_snapshot('op-snapshot-id')

        with tools.assert_raises(iaas_error.ProviderDeleteSnapshotError):
            op_api.do_delete_snapshot('op-snapshot-id')

    @patch('neutronclient.v2_0.client.Client.create_router')
    def test_do_create_router(self, router_create):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_create_router))
        mock.router['id'] = '1234-asdf'
        router_create.side_effect = [mock, exc]

        router0 = op_api.do_create_router('op-project-id', 'name')
        tools.eq_(router0['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderCreateRouterError):
            op_api.do_create_router('op-project-id', 'name')

    @patch('neutronclient.v2_0.client.Client.create_network')
    def test_do_create_network(self, network_create):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_create_network))
        mock.network['id'] = '1234-asdf'
        network_create.side_effect = [mock, exc]

        network0 = op_api.do_create_network('op-project-id', 'name')
        tools.eq_(network0['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderCreateNetworkError):
            op_api.do_create_network('op-project-id', 'name')

    @patch('neutronclient.v2_0.client.Client.delete_router')
    def test_do_delete_router(self, router_delete):
        router_delete.side_effect = [None, exc]

        op_api.do_delete_router('op-router-id')

        with tools.assert_raises(iaas_error.ProviderDeleteRouterError):
            op_api.do_delete_router('op-router-id')

    @patch('neutronclient.v2_0.client.Client.delete_network')
    def test_do_delete_network(self, network_delete):
        network_delete.side_effect = [None, exc]

        op_api.do_delete_network('op-network-id')

        with tools.assert_raises(iaas_error.ProviderDeleteNetworkError):
            op_api.do_delete_network('op-network-id')

    @patch('neutronclient.v2_0.client.Client.add_gateway_router')
    @patch('neutronclient.v2_0.client.Client.list_networks')
    def test_do_set_gateway_router(self, networks_list, gw_router_add):
        mock1 = MockObject(**copy.copy(op_fixtures.op_mock_list_networks))
        networks_list.return_value = mock1

        mock2 = MockObject(**copy.copy(op_fixtures.op_mock_add_gateway_router))
        mock2.router['id'] = '1234-asdf'
        gw_router_add.side_effect = [mock2, exc]

        router0 = op_api.do_set_gateway_router('op-router-id', 10)
        tools.eq_(router0['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderAddGatewayRouterError):
            op_api.do_set_gateway_router('op-router-id', 10)

    @patch('neutronclient.v2_0.client.Client.remove_gateway_router')
    def test_do_remove_gateway_router(self, gw_router_remove):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_remove_gateway_router))  # noqa
        mock.router['id'] = '1234-asdf'
        gw_router_remove.side_effect = [mock, exc]

        op_api.do_remove_gateway_router('op-router-id')

        with tools.assert_raises(iaas_error.ProviderRemoveGatewayRouterError):
            op_api.do_remove_gateway_router('op-router-id')

    @patch('neutronclient.v2_0.client.Client.list_networks')
    def test_do_get_network(self, networks_list):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_list_networks))
        mock.networks[0]['id'] = '1234-asdf'
        networks_list.side_effect = [mock, exc]

        network0 = op_api.do_get_network('op-network-id')
        tools.eq_(network0['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderGetNetworkError):
            op_api.do_get_network('op-network-id')

    @patch('neutronclient.v2_0.client.Client.list_routers')
    def test_do_get_router(self, routers_list):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_list_routers))
        mock.routers[0]['id'] = '1234-asdf'
        routers_list.side_effect = [mock, exc]

        router0 = op_api.do_get_router('op-router-id')
        tools.eq_(router0['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderGetRouterError):
            op_api.do_get_router('op-router-id')

    @patch('neutronclient.v2_0.client.Client.list_ports')
    def test_do_list_ports(self, ports_list):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_list_ports))
        mock.ports[0]['id'] = '1234-asdf'
        ports_list.side_effect = [mock, exc]

        ports = op_api.do_list_ports('op-network-id')
        tools.eq_(ports[0]['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderListPortsError):
            op_api.do_list_ports('op-network-id')

    @patch('neutronclient.v2_0.client.Client.put')
    def test_do_add_port_forwarding(self, pf_add):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_port_forwarding))
        mock.id = '1234-asdf'
        pf_add.side_effect = [mock, exc]

        pf = op_api.do_add_port_forwarding('op-router-id',
                                           'tcp', 2222, '192.168.1.101', 22)
        tools.eq_(pf['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderAddPortForwardingError):
            op_api.do_add_port_forwarding('op-router-id',
                                          'tcp', 2222, '192.168.1.101', 22)

    @patch('neutronclient.v2_0.client.Client.put')
    def test_do_remove_port_forwarding(self, pf_remove):
        pf_remove.side_effect = [None, exc]

        op_api.do_remove_port_forwarding('op-router-id', 'op-pf-id')

        with tools.assert_raises(iaas_error.ProviderRemovePortForwardingError):
            op_api.do_remove_port_forwarding('op-router-id', 'op-pf-id')

    @patch('neutronclient.v2_0.client.Client.create_subnet')
    def test_do_create_subnet(self, subnet_create):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_subnet))
        mock.subnet['id'] = '1234-asdf'
        subnet_create.side_effect = [mock, exc]

        subnet0 = op_api.do_create_subnet('op-project-id', 'op-network-id',
                                          'name', '192.168.1.1/24')
        tools.eq_(subnet0['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderCreateSubnetError):
            op_api.do_create_subnet('op-project-id', 'op-network-id',
                                    'name', '192.168.1.1/24')

    @patch('neutronclient.v2_0.client.Client.delete_subnet')
    def test_do_delete_subnet(self, subnet_delete):
        subnet_delete.side_effect = [None, exc]

        op_api.do_delete_subnet('op-subnet-id')

        with tools.assert_raises(iaas_error.ProviderDeleteSubnetError):
            op_api.do_delete_subnet('op-subnet-id')

    @patch('neutronclient.v2_0.client.Client.remove_interface_router')
    def test_do_detach_subnet(self, interface_router_remove):
        interface_router_remove.side_effect = [None, exc]

        op_api.do_detach_subnet('op-subnet-id', 'op-router-id')

        with tools.assert_raises(iaas_error.ProviderDetachSubnetError):
            op_api.do_detach_subnet('op-subnet-id', 'op-router-id')

    @patch('neutronclient.v2_0.client.Client.add_interface_router')
    def test_do_attach_subnet(self, interface_router_add):
        interface_router_add.side_effect = [None, exc]

        op_api.do_attach_subnet('op-subnet-id', 'op-router-id')

        with tools.assert_raises(iaas_error.ProviderAttachSubnetError):
            op_api.do_attach_subnet('op-subnet-id', 'op-router-id')

    @patch('neutronclient.v2_0.client.Client.create_floatingip')
    @patch('neutronclient.v2_0.client.Client.list_networks')
    def test_do_create_floatingip(self, networks_list, floatingip_create):
        mock1 = MockObject(**copy.copy(op_fixtures.op_mock_list_networks))
        networks_list.return_value = mock1

        mock = MockObject(**copy.copy(op_fixtures.op_mock_floatingip))
        mock.floatingip['id'] = '1234-asdf'
        floatingip_create.side_effect = [mock, exc]

        fip0 = op_api.do_create_floatingip('op-project-id', 10)
        tools.eq_(fip0['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderCreateFloatingipError):
            op_api.do_create_floatingip('op-project-id', 10)

    @patch('neutronclient.v2_0.client.Client.update_floatingip')
    def test_do_update_floatingip_rate_limit(self, floatingip_update):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_floatingip))
        mock.floatingip['id'] = '1234-asdf'
        floatingip_update.side_effect = [mock, exc]

        op_api.do_update_floatingip_rate_limit('op-floatingip-id', 10)

        with tools.assert_raises(iaas_error.ProviderUpdateFloatingipError):
            op_api.do_update_floatingip_rate_limit('op-floatingip-id', 10)

    @patch('neutronclient.v2_0.client.Client.update_floatingip')
    def test_do_update_floatingip_port(self, floatingip_update):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_floatingip))
        mock.floatingip['id'] = '1234-asdf'
        floatingip_update.side_effect = [mock, exc]

        op_api.do_update_floatingip_port('op-floatingip-id', 'port-id')

        with tools.assert_raises(iaas_error.ProviderUpdateFloatingipPortError):
            op_api.do_update_floatingip_port('op-floatingip-id', 'port-id')

    @patch('neutronclient.v2_0.client.Client.delete_floatingip')
    def test_do_delete_floatingip(self, floatingip_delete):
        floatingip_delete.side_effect = [None, exc]

        op_api.do_delete_floatingip('op-floatingip-id')

        with tools.assert_raises(iaas_error.ProviderDeleteFloatingipError):
            op_api.do_delete_floatingip('op-floatingip-id')

    @patch('neutronclient.v2_0.client.Client.list_floatingips')
    def test_do_list_floatingips(self, floatingips_list):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_list_floatingips))
        mock.floatingips[0]['id'] = '1234-asdf'
        floatingips_list.side_effect = [mock, exc]

        floatingips = op_api.do_list_floatingips()
        tools.eq_(floatingips[0]['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderListFloatingipsError):
            op_api.do_list_floatingips()

    @patch('neutronclient.v2_0.client.Client.list_routers')
    def test_do_list_routers(self, routers_list):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_list_routers))
        mock.routers[0]['id'] = '1234-asdf'
        routers_list.side_effect = [mock, exc]

        routerss = op_api.do_list_routers()
        tools.eq_(routerss[0]['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderListRoutersError):
            op_api.do_list_routers()

    @patch('neutronclient.v2_0.client.Client.list_networks')
    def test_do_get_public_network(self, networks_list):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_list_networks))
        mock.networks[0]['id'] = '1234-asdf'
        networks_list.side_effect = [mock, None, exc]

        fip0 = op_api.do_get_public_network()
        tools.eq_(fip0['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderGetPublicNetworkError) as cm:  # noqa
            op_api.do_get_public_network()
        tools.eq_(str(cm.exception.exception), 'Public network is not found.')

        with tools.assert_raises(iaas_error.ProviderGetPublicNetworkError):
            op_api.do_get_public_network()

    @patch('neutronclient.v2_0.client.Client.list_subnets')
    def test_do_list_subnets(self, subnets_list):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_list_subnets))
        mock.subnets[0]['id'] = '1234-asdf'
        subnets_list.side_effect = [mock, exc]

        subnets = op_api.do_list_subnets('op-network-id', False)
        tools.eq_(subnets[0]['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderListSubnetsError):
            op_api.do_list_subnets('op-network-id', False)

    @patch('novaclient.v2.flavors.FlavorManager.find')
    def test_do_find_flavor(self, flavor_find):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_flavor))
        mock.id = '1234-asdf'
        flavor_find.side_effect = [mock, exc]

        flavor = op_api.do_find_flavor('intance-type-id')
        tools.eq_(flavor['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderFindFlavorError):
            op_api.do_find_flavor('intance-type-id')

    @patch('novaclient.v2.flavors.FlavorManager.create')
    def test_do_create_flavor(self, flavor_create):
        mock = MockObject(**copy.copy(op_fixtures.op_mock_flavor))
        mock.id = '1234-asdf'
        flavor_create.side_effect = [mock, exc]

        flavor = op_api.do_create_flavor('name', 1024, 10, 40, 'op-flavor-id')
        tools.eq_(flavor['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderCreateFlavorError):
            op_api.do_create_flavor('name', 1024, 10, 40, 'op-flavor-id')

    @patch('novaclient.v2.flavors.FlavorManager.get')
    def test_do_update_flavor_quota(self, flavor_get):
        mock1 = MockObject(**copy.copy(op_fixtures.op_mock_flavor))
        mock1.id = '1234-asdf'
        flavor_get.return_value = mock1

        mock2 = MagicMock()
        mock2.side_effect = [None, exc]

        # set_keys function is another mock object.
        # when set_keys() called mutil-times:
        #       first time return None, second time raise exception
        mock1.set_keys = mock2

        op_api.do_update_flavor_quota('op-flavor-id', 40, 40, 40, 40, 4, 4)

        with tools.assert_raises(iaas_error.ProviderUpdateFlavorQuotaError):
            op_api.do_update_flavor_quota('op-flavor-id', 40, 40, 40, 40, 4, 4)

    @patch('novaclient.v2.flavors.FlavorManager.delete')
    def test_do_delete_flavor(self, flavor_delete):
        flavor_delete.side_effect = [None, exc]

        op_api.do_delete_flavor('op-flavor-id')

        with tools.assert_raises(iaas_error.ProviderDeleteFlavorError):
            op_api.do_delete_flavor('op-flavor-id')

    @patch('novaclient.v2.hypervisors.HypervisorManager.findall')
    def test_do_list_hypervisors(self, hypervisors_findall):
        mock = [MockObject(**copy.copy(op_fixtures.op_mock_hypervisor))]
        mock[0].id = '1234-asdf'
        hypervisors_findall.side_effect = [mock, exc]

        hypervisors = op_api.do_list_hypervisors()
        tools.eq_(hypervisors[0]['id'], '1234-asdf')

        with tools.assert_raises(iaas_error.ProviderListHypervisorsError):
            op_api.do_list_hypervisors()

    @patch('ceilometerclient.v2.statistics.StatisticsManager.list')
    @patch('ceilometerclient.client.SessionClient.request')
    def test_do_statistics(self, client_request, statistics_list):
        client_request.return_value = MockObject()
        statistics_list.side_effect = [op_fixtures.op_mock_list_statistics,
                                       exc]

        op_api.do_statistics(
            'meter', 'op_resource_id', 'op_project_id', 'aggregation',
            'period', 'start', 'end')

        with tools.assert_raises(iaas_error.ProviderStatisticsError):
            op_api.do_statistics(
                'meter', 'op_resource_id', 'op_project_id', 'aggregation',
                'period', 'start', 'end')
