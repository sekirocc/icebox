import env  # noqa
import patches
import fixtures
import fixtures_openstack as op_fixtures
import json
from mock import patch
from nose import tools
from densefog.common import utils
from densefog.model.job import job as job_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import subnet as subnet_model
from icebox.model.iaas import port_forwarding as pf_model
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import eip as eip_model
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import subnet_resource as subres_model

project_id_1 = 'prjct-1234'


def create_instance(instance_id, network_id, status=instance_model.INSTANCE_STATUS_ACTIVE):  # noqa
    rand_id = utils.generate_key(32)
    fixtures.insert_instance_type(project_id=project_id_1, instance_type_id=rand_id)  # noqa
    fixtures.insert_image(project_id=project_id_1, image_id=rand_id)

    subnet_id = utils.generate_key(10)
    fixtures.insert_subnet(project_id=project_id_1,
                           network_id=network_id, subnet_id=subnet_id)
    fixtures.insert_instance(project_id=project_id_1, instance_id=instance_id,
                             network_id=network_id, subnet_id=subnet_id,
                             status=status)
    return instance_id


def mock_get_network(*args, **kwargs):
    return op_fixtures.op_mock_get_network['network']


def mock_create_network(*args, **kwargs):
    return op_fixtures.op_mock_create_network['network']


def mock_create_router(*args, **kwargs):
    return op_fixtures.op_mock_create_router['router']


def mock_list_ports(*args, **kwargs):
    return op_fixtures.op_mock_list_ports['ports']


def mock_list_networks(*args, **kwargs):
    return op_fixtures.op_mock_list_networks['networks']


def mock_list_routers(*args, **kwargs):
    return op_fixtures.op_mock_list_routers['routers']


def mock_get_router(*args, **kwargs):
    return op_fixtures.op_mock_get_router['router']


def mock_set_gateway_router(*args, **kwargs):
    return op_fixtures.op_mock_add_gateway_router['router']


def mock_remove_gateway_router(*args, **kwargs):
    return op_fixtures.op_mock_remove_gateway_router['router']


def mock_nope(*args, **kwargs):
    pass


@patches.nova_authenticate
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('icebox.model.iaas.openstack.api.do_create_router', mock_create_router)            # noqa
    @patch('icebox.model.iaas.openstack.api.do_create_network', mock_create_network)          # noqa
    def test_create(self):
        network_model.create(project_id=project_id_1, description='')
        tools.eq_(job_model.limitation()['total'], 1)

    @patch('icebox.model.iaas.openstack.api.do_set_gateway_router', mock_set_gateway_router)  # noqa
    def test_set_external_gateway(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        network_model.set_external_gateway(project_id_1, [network_id], bandwidth=100)   # noqa

        network = network_model.get(network_id)

        tools.assert_not_equal(network['external_gateway_ip'], '')
        tools.eq_(network['external_gateway_bandwidth'], 100)

    @patch('icebox.model.iaas.openstack.api.do_remove_gateway_router', mock_nope)         # noqa
    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_port', mock_nope)  # noqa
    def test_unset_external_gateway(self):
        network_id = 'network-id-aa'
        fixtures.insert_network(project_id=project_id_1, network_id=network_id)

        # create a instance in this network
        instance_id = create_instance('instance-id-a', network_id)
        # set the network's gateway
        network_model.Network.update(network_id, **{
            'external_gateway_ip': '10.10.10.10',
            'external_gateway_bandwidth': 100,
        })

        # create eip and bind instance to it
        eip_id = fixtures.insert_eip(project_id=project_id_1)
        eip_model.associate(project_id_1, eip_id, instance_id)

        with tools.assert_raises(iaas_error.RemoveExternalGatewayWhenInstancesBindingEip):   # noqa
            network_model.unset_external_gateway(project_id_1, [network_id])

        # unbind instance with eip
        eip_model.dissociate(project_id_1, [eip_id])
        # now can remove
        network_model.unset_external_gateway(project_id_1, [network_id])

        network = network_model.get(network_id)
        tools.eq_(network['external_gateway_ip'], '')
        tools.eq_(network['external_gateway_bandwidth'], 0)

    def test_limitation(self):
        network_id = fixtures.insert_network(project_id=project_id_1)

        tools.eq_(network_model.limitation(
            project_ids=[project_id_1])['total'], 1)
        tools.eq_(network_model.limitation(
            project_ids=[])['total'], 0)

        tools.eq_(network_model.limitation(
            status=[network_model.NETWORK_STATUS_PENDING])['total'], 1)
        tools.eq_(network_model.limitation(
            status=[network_model.NETWORK_STATUS_DELETED])['total'], 0)

        tools.eq_(network_model.limitation(
            network_ids=[network_id])['total'], 1)
        tools.eq_(network_model.limitation(
            network_ids=[])['total'], 0)

        tools.eq_(network_model.limitation(
            search_word=network_id)['total'], 1)

    def test_delete(self):
        network_id = 'network-id-aa'
        fixtures.insert_network(project_id=project_id_1, network_id=network_id,
                                status=network_model.NETWORK_STATUS_ACTIVE)
        network_model.delete(project_id_1, [network_id])

    def test_delete_with_status(self):
        network_id = 'network-id-aa'
        fixtures.insert_network(project_id=project_id_1, network_id=network_id,
                                status=network_model.NETWORK_STATUS_ACTIVE)
        # we can delete active network.
        network_model.delete(project_id_1, [network_id])

        network_id = 'network-id-bb'
        fixtures.insert_network(project_id=project_id_1, network_id=network_id,
                                status=network_model.NETWORK_STATUS_PENDING)

        # we can not delete pending network.
        with tools.assert_raises(iaas_error.NetworkCanNotDelete):   # noqa
            network_model.delete(project_id_1, [network_id])

    def test_delete_with_instances_in_network(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_ACTIVE)
        create_instance('instance-id-a', 'net-aaa',
                        status=instance_model.INSTANCE_STATUS_DELETED)  # noqa
        # there is an deleted instance in network. but we can delete network.
        network_model.delete(project_id_1, ['net-aaa'])

        fixtures.insert_network(project_id=project_id_1, network_id='net-bbb',
                                status=network_model.NETWORK_STATUS_ACTIVE)
        create_instance('instance-id-c', 'net-bbb')
        create_instance('instance-id-d', 'net-bbb')
        # there are some active instance in network. can not delete
        with tools.assert_raises(iaas_error.DeleteNetworkWhenInstancesInSubnet):   # noqa
            network_model.delete(project_id_1, ['net-bbb'])

    def test_delete_with_external_gateway(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_ACTIVE)
        network_model.Network.update('net-aaa',
                                     external_gateway_ip='10.167.200.1')
        # the network has external gateway. can not delete
        with tools.assert_raises(iaas_error.DeleteNetworkWhenHasExternalGateway):   # noqa
            network_model.delete(project_id_1, ['net-aaa'])

    def test_delete_with_resources_erased(self):
        fixtures.insert_network(project_id=project_id_1,
                                network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_ACTIVE)
        fixtures.insert_subnet(project_id=project_id_1,
                               network_id='net-aaa',
                               subnet_id='sub-aaa')
        fixtures.insert_port_forwarding(project_id=project_id_1,
                                        network_id='net-aaa',
                                        port_forwarding_id='pf-aaa')

        network_model.delete(project_id_1, ['net-aaa'])

        job = job_model.limitation(
            limit=0, run_at=utils.seconds_later(11))['items'][0]

        tools.eq_(job['action'], 'EraseNetworks')
        tools.eq_(json.loads(job['params'])['resource_ids'][0], 'net-aaa')

    @patch('icebox.model.iaas.waiter.wait_port_deleted', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_list_ports', mock_list_ports)
    @patch('icebox.model.iaas.openstack.api.do_delete_port', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_detach_subnet', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_delete_subnet', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_remove_port_forwarding', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_delete_router', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_delete_network', mock_nope)
    def test_erase(self):
        fixtures.insert_network(project_id=project_id_1,
                                network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_DELETED)
        fixtures.insert_subnet(project_id=project_id_1,
                               network_id='net-aaa',
                               subnet_id='sub-aaa')
        fixtures.insert_port_forwarding(project_id=project_id_1,
                                        network_id='net-aaa',
                                        port_forwarding_id='pf-aaa')

        network_model.erase('net-aaa')

        tools.assert_equal(bool(network_model.get('net-aaa')['ceased']), True)

        tools.eq_(pf_model.get('pf-aaa')['status'],
                  pf_model.PORT_FORWARDING_STATUS_DELETED)
        tools.eq_(subnet_model.get('sub-aaa')['status'],
                  subnet_model.SUBNET_STATUS_DELETED)

    @patch('icebox.model.iaas.openstack.api.do_get_network', mock_get_network)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_get_router', mock_get_router)
    def test_sync(self):
        fixtures.insert_network(project_id=project_id_1,
                                network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_PENDING)
        network_model.sync('net-aaa')

        tools.eq_(network_model.get('net-aaa')['status'],
                  network_model.NETWORK_STATUS_ACTIVE)


@patches.nova_authenticate
@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_public_describe_networks(self):
        fixtures.insert_network(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeNetworks'
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(1, json.loads(result.data)['data']['total'])

    def test_public_describe_networks_with_status(self):
        fixtures.insert_network(
            project_id=project_id_1, network_id='net-aaa',
            status=network_model.NETWORK_STATUS_ACTIVE)
        fixtures.insert_network(
            project_id=project_id_1, network_id='net-bbb',
            status=network_model.NETWORK_STATUS_PENDING)
        fixtures.insert_network(
            project_id=project_id_1, network_id='net-ccc',
            status=network_model.NETWORK_STATUS_DELETED)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeNetworks',
                'status': status
            }))
            return result

        result = send_request([network_model.NETWORK_STATUS_ACTIVE,
                               network_model.NETWORK_STATUS_PENDING])

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    @patch('icebox.model.iaas.openstack.api.do_create_network', mock_create_network)    # noqa
    @patch('icebox.model.iaas.openstack.api.do_create_router', mock_create_router)      # noqa
    def test_public_create_network(self):
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'CreateNetwork',
        }))

        tools.eq_(0, json.loads(result.data)['retCode'])

        data = json.loads(result.data)['data']

        tools.assert_not_equal(data['networkId'], None)
        tools.assert_not_equal(data['jobId'], None)

    def test_public_delete_network(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteNetworks',
            'networkIds': [network_id],
        }))
        tools.eq_(4105, json.loads(result.data)['retCode'])

        network_model.Network.update(
            network_id,
            status=network_model.NETWORK_STATUS_ACTIVE
        )

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteNetworks',
            'networkIds': [network_id],
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        tools.eq_(network_model.limitation(
            status=[network_model.NETWORK_STATUS_DELETED])['total'], 1)

    def test_public_delete_network_with_instances_in_network(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_ACTIVE)
        create_instance('instance-id-c', 'net-aaa')
        create_instance('instance-id-d', 'net-aaa')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteNetworks',
            'networkIds': ['net-aaa'],
        }))
        tools.eq_(4732, json.loads(result.data)['retCode'])

    def test_delete_network_with_external_gateway(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_ACTIVE)
        network_model.Network.update('net-aaa',
                                     external_gateway_ip='10.167.200.1')
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteNetworks',
            'networkIds': ['net-aaa'],
        }))
        tools.eq_(4734, json.loads(result.data)['retCode'])

    def test_modify_network_attributes(self):
        network_id = fixtures.insert_network(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ModifyNetworkAttributes',
            'networkId': network_id,
            'name': 'nw_123',
            'description': 'desc_123',
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        network = network_model.limitation(network_ids=[network_id])['items'][0]   # noqa
        tools.eq_(network['name'], 'nw_123')
        tools.eq_(network['description'], 'desc_123')

    @patch('icebox.model.iaas.openstack.api.do_set_gateway_router', mock_set_gateway_router)  # noqa
    def test_public_set_external_gateway(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'SetExternalGateway',
            'networkIds': [network_id],
            'bandwidth': 100,
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        network = network_model.get(network_id)

        tools.assert_not_equal(network['external_gateway_ip'], '')
        tools.eq_(network['external_gateway_bandwidth'], 100)

    @patch('icebox.model.iaas.openstack.api.do_set_gateway_router', mock_set_gateway_router)  # noqa
    def test_public_update_external_gateway_bandwidth(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'SetExternalGateway',
            'networkIds': [network_id],
            'bandwidth': 100,
        }))
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'UpdateExternalGatewayBandwidth',
            'networkIds': [network_id],
            'bandwidth': 200,
        }))

        tools.eq_(0, json.loads(result.data)['retCode'])

        network = network_model.get(network_id)
        tools.eq_(network['external_gateway_bandwidth'], 200)

    @patch('icebox.model.iaas.openstack.api.do_remove_gateway_router', mock_remove_gateway_router)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_port', mock_nope)  # noqa
    def test_public_unset_external_gateway(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-aaa')

        # create a instance in this network
        create_instance('inst-aaa', 'net-aaa')

        # set the network's gateway
        network_model.Network.update('net-aaa', **{
            'external_gateway_ip': '10.10.10.10',
            'external_gateway_bandwidth': 100,
        })

        # create eip and bind instance to it
        fixtures.insert_eip(project_id=project_id_1, eip_id='eip-aaa')
        eip_model.associate(project_id_1, 'eip-aaa', 'inst-aaa')

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'UnsetExternalGateway',
                'networkIds': ['net-aaa'],
            }))
            return result

        result = send_request()
        data = json.loads(result.data)
        # it will fail because the instance binds to an eip.
        tools.eq_(4731, data['retCode'])
        tools.eq_('inst-aaa', data['data']['instanceIds'][0])

        # unbind the instance from eip
        eip_model.dissociate(project_id_1, ['eip-aaa'])

        result = send_request()
        data = json.loads(result.data)
        # it will success
        tools.eq_(0, data['retCode'])

        network = network_model.get('net-aaa')

        tools.eq_(network['external_gateway_ip'], '')
        tools.eq_(network['external_gateway_bandwidth'], 0)

    @patches.check_manage()
    def test_manage_describe_subnets(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        fixtures.insert_subnet(
            subnet_id='sbt-1',
            project_id=project_id_1, network_id=network_id,
            cidr='192.168.200.0/24')
        fixtures.insert_subnet(
            subnet_id='sbt-2',
            project_id=project_id_1, network_id=network_id,
            cidr='192.168.210.0/24')
        fixtures.insert_subnet(
            subnet_id='sbt-3',
            project_id=project_id_1, network_id=network_id,
            cidr='192.168.220.0/24')

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeSubnets',
            'networkIds': [network_id],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])

        subnets = data['data']['subnetSet']

        tools.eq_(3, len(subnets))
        tools.assert_not_equal(subnets[0]['opSubnetId'], '')
        tools.assert_not_equal(subnets[1]['opSubnetId'], '')
        tools.assert_not_equal(subnets[2]['opSubnetId'], '')

    @patches.check_manage()
    def test_manage_add_subnet_resources(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id,
            cidr='192.168.200.0/24')

        def send_request(resource_type, resource_ids):
            result = fixtures.manage.post('/', data=json.dumps({
                'action': 'AddSubnetResources',
                'subnetId': subnet_id,
                'resourceType': resource_type,
                'resourceIds': resource_ids
            }))
            return result

        load_balancers = ['lb-1', 'lb-2', 'lb-3']
        servers = ['svr-1', 'svr-2', 'svr-3']

        result = send_request(
            subnet_model.RESOURCE_TYPE_LOAD_BALANCER,
            load_balancers)
        data = json.loads(result.data)['data']
        tools.eq_(load_balancers, data['resourceIds'])

        result = send_request(
            subnet_model.RESOURCE_TYPE_SERVER,
            servers)
        data = json.loads(result.data)['data']
        tools.eq_(servers, data['resourceIds'])

        page = subres_model.limitation(subnet_ids=[subnet_id])['items']
        tools.eq_(6, len(page))

    @patches.check_manage()
    def test_manage_rem_subnet_resources(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id,
            cidr='192.168.200.0/24')

        load_balancers = ['lb-1', 'lb-2', 'lb-3']
        servers = ['svr-1', 'svr-2', 'svr-3']

        fixtures.insert_subnet_resources(
            subnet_id=subnet_id,
            resource_ids=load_balancers,
            resource_type=subnet_model.RESOURCE_TYPE_LOAD_BALANCER
        )
        fixtures.insert_subnet_resources(
            subnet_id=subnet_id,
            resource_ids=servers,
            resource_type=subnet_model.RESOURCE_TYPE_SERVER
        )

        def send_request(resource_type, resource_ids):
            result = fixtures.manage.post('/', data=json.dumps({
                'action': 'RemSubnetResources',
                'resourceType': resource_type,
                'resourceIds': resource_ids
            }))
            return result

        rem_load_balancers = ['lb-1']
        rem_servers = ['svr-1']

        result1 = send_request(subnet_model.RESOURCE_TYPE_LOAD_BALANCER,
                               rem_load_balancers)
        result2 = send_request(subnet_model.RESOURCE_TYPE_SERVER,
                               rem_servers)
        tools.eq_(rem_load_balancers,
                  json.loads(result1.data)['data']['resourceIds'])
        tools.eq_(rem_servers,
                  json.loads(result2.data)['data']['resourceIds'])

        # insert 6 resources, remove 2 resources, left 4 resources.
        page = subres_model.limitation(subnet_ids=[subnet_id])['items']
        tools.eq_(4, len(page))
