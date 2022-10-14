import env  # noqa
import patches
import json
from mock import patch
from nose import tools
from densefog.common import utils
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import subnet as subnet_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import error as iaas_error

import fixtures
import fixtures_openstack as op_fixtures

project_id_1 = 'prjct-1234'
cidr_1 = u'192.168.0.0/24'


def create_instance(network_id, subnet_id, status):
    instance_id = utils.generate_key(10)
    rand_id = utils.generate_key(10)
    fixtures.insert_instance_type(project_id=project_id_1, instance_type_id=rand_id)  # noqa
    fixtures.insert_image(project_id=project_id_1, image_id=rand_id)

    network_id = utils.generate_key(10)
    fixtures.insert_instance(project_id=project_id_1, instance_id=instance_id,
                             network_id=network_id, subnet_id=subnet_id,
                             status=status)
    return instance_id


def mock_create_subnet(*args, **kwargs):
    return op_fixtures.op_mock_subnet['subnet']


def mock_nope(*args, **kwargs):
    return True


@patches.nova_authenticate
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('icebox.model.iaas.openstack.api.do_create_subnet', mock_create_subnet)   # noqa
    @patch('icebox.model.iaas.openstack.api.do_attach_subnet', mock_nope)            # noqa
    def test_create(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)

        subnet_model.create(
            project_id=project_id_1,
            network_id=network_id,
            cidr=cidr_1)

    def test_limitation(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id,
            cidr='192.168.200.0/24')

        tools.eq_(subnet_model.limitation(
            project_ids=[project_id_1])['total'], 1)
        tools.eq_(subnet_model.limitation(
            project_ids=[])['total'], 0)

        tools.eq_(subnet_model.limitation(
            network_ids=[network_id])['total'], 1)

        tools.eq_(subnet_model.limitation(
            status=[subnet_model.SUBNET_STATUS_ACTIVE])['total'], 1)
        tools.eq_(subnet_model.limitation(
            status=[subnet_model.SUBNET_STATUS_DELETED])['total'], 0)

        tools.eq_(subnet_model.limitation(
            subnet_ids=[subnet_id])['total'], 1)
        tools.eq_(subnet_model.limitation(
            subnet_ids=[])['total'], 0)

        tools.eq_(subnet_model.limitation(
            search_word=subnet_id)['total'], 1)
        tools.eq_(subnet_model.limitation(
            search_word='192.168.200')['total'], 1)
        tools.eq_(subnet_model.limitation(
            search_word='192.168.200.0')['total'], 1)
        tools.eq_(subnet_model.limitation(
            search_word='192.168.100')['total'], 0)

        tools.eq_(network_model.limitation(
            verbose=True)['total'], 1)

        tools.eq_(len(network_model.limitation(
            verbose=True)['items'][0]['subnets']), 1)

    def test_delete(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)

        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id)

        subnet_model.delete(project_id_1, subnet_ids=[subnet_id])

        tools.eq_(subnet_model.limitation(
            project_ids=[project_id_1])['total'], 1)
        tools.eq_(subnet_model.limitation(
            status=[subnet_model.SUBNET_STATUS_DELETED])['total'], 1)

    def test_delete_with_status(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-1',
                                status=network_model.NETWORK_STATUS_ACTIVE)

        fixtures.insert_subnet(project_id=project_id_1,
                               network_id='net-1', subnet_id='snt-1',
                               status=subnet_model.SUBNET_STATUS_ACTIVE)

        # we can delete active subnet
        subnet_model.delete(project_id_1, subnet_ids=['snt-1'])

        fixtures.insert_subnet(project_id=project_id_1,
                               network_id='net-1', subnet_id='snt-2',
                               status=subnet_model.SUBNET_STATUS_DELETED)

        # we can not delete deleted subnet
        with tools.assert_raises(iaas_error.SubnetCanNotDelete):
            subnet_model.delete(project_id_1, subnet_ids=['snt-2'])

    def test_delete_with_instance_in_subnet(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-1',
                                status=network_model.NETWORK_STATUS_ACTIVE)
        fixtures.insert_subnet(project_id=project_id_1,
                               network_id='net-1', subnet_id='snt-1',
                               status=subnet_model.SUBNET_STATUS_ACTIVE)

        create_instance('net-1', 'snt-1', instance_model.INSTANCE_STATUS_DELETED)   # noqa
        # there is an deleted instance in subnet. but we can delete the subnet.
        subnet_model.delete(project_id_1, subnet_ids=['snt-1'])

        fixtures.insert_subnet(project_id=project_id_1,
                               network_id='net-1', subnet_id='snt-2',
                               status=subnet_model.SUBNET_STATUS_ACTIVE)

        create_instance('net-1', 'snt-2', instance_model.INSTANCE_STATUS_ACTIVE)   # noqa
        # there is an active instance in subnet, we cannot delete the subnet.
        with tools.assert_raises(iaas_error.DeleteSubnetWhenInstancesInSubnet):
            subnet_model.delete(project_id_1, subnet_ids=['snt-2'])

    @patch('icebox.model.iaas.openstack.api.do_delete_subnet', mock_create_subnet)   # noqa
    @patch('icebox.model.iaas.openstack.api.do_detach_subnet', mock_nope)            # noqa
    def test_erase(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)

        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id,
            status=subnet_model.SUBNET_STATUS_DELETED)

        subnet_model.erase(subnet_id)

        tools.assert_equal(bool(subnet_model.get(subnet_id)['ceased']),
                           True)

    def test_modify(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id)

        # should not modify other's subnet
        fixtures.insert_project('project_id_b')
        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            subnet_model.modify('project_id_b', subnet_id, 'new-subnet-name')  # noqa

        # modify success
        subnet_model.modify(project_id_1, subnet_id, 'new-subnet-name')

        tools.eq_(subnet_model.get(subnet_id)['name'], 'new-subnet-name')

    def test_count_instances(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-1')
        fixtures.insert_subnet(project_id=project_id_1, network_id='net-1', subnet_id='snt-1')  # noqa

        create_instance('net-1', 'snt-1', instance_model.INSTANCE_STATUS_PENDING)   # noqa
        create_instance('net-1', 'snt-1', instance_model.INSTANCE_STATUS_ACTIVE)   # noqa
        create_instance('net-1', 'snt-1', instance_model.INSTANCE_STATUS_STARTING)   # noqa
        create_instance('net-1', 'snt-1', instance_model.INSTANCE_STATUS_DELETED)   # noqa
        create_instance('net-1', 'snt-1', instance_model.INSTANCE_STATUS_CEASED)   # noqa

        count = subnet_model.count_instances('snt-1')
        tools.eq_(count, 3)


@patches.nova_authenticate
@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_describe_subnets(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeSubnets'
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(1, json.loads(result.data)['data']['total'])

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeSubnets',
            'subnetIds': [subnet_id],
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(1, json.loads(result.data)['data']['total'])

        network_id = subnet_model.limitation()['items'][0]['network_id']
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeSubnets',
            'networkIds': [network_id],
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(1, json.loads(result.data)['data']['total'])

    def test_describe_subnets_with_status(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id, subnet_id='snt-aaa',  # noqa
            status=subnet_model.SUBNET_STATUS_ACTIVE)
        fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id, subnet_id='snt-bbb',  # noqa
            status=subnet_model.SUBNET_STATUS_ACTIVE)
        fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id, subnet_id='snt-ccc',  # noqa
            status=subnet_model.SUBNET_STATUS_DELETED)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeSubnets',
                'status': status
            }))
            return result

        result = send_request([subnet_model.SUBNET_STATUS_ACTIVE])

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    @patch('icebox.model.iaas.openstack.api.do_create_subnet', mock_create_subnet)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_attach_subnet', mock_nope)           # noqa
    def test_create_subnet(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'CreateSubnet',
            'networkId': network_id,
            'cidr': cidr_1,
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        subnet_id = json.loads(result.data)['data']['subnetId']

        tools.eq_(subnet_id, json.loads(result.data)['data']['subnetId'])

    def test_delete_subnet(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)

        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteSubnets',
            'subnetIds': [subnet_id],
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        tools.eq_(subnet_model.limitation(
            status=[subnet_model.SUBNET_STATUS_DELETED])['total'], 1)

    def test_delete_subnet_with_instance_in_subnet(self):
        fixtures.insert_network(
            project_id=project_id_1, network_id='net-1',
            status=network_model.NETWORK_STATUS_ACTIVE)

        fixtures.insert_subnet(project_id=project_id_1,
                               network_id='net-1', subnet_id='snt-1',
                               status=subnet_model.SUBNET_STATUS_ACTIVE)
        create_instance('net-1', 'snt-1', instance_model.INSTANCE_STATUS_ACTIVE)   # noqa
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteSubnets',
            'subnetIds': ['snt-1'],
        }))
        tools.eq_(4741, json.loads(result.data)['retCode'])

    def test_modify_subnet_attributes(self):
        network_id = fixtures.insert_network(project_id=project_id_1)
        subnet_id = fixtures.insert_subnet(
            project_id=project_id_1, network_id=network_id)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ModifySubnetAttributes',
            'subnetId': subnet_id,
            'name': 'new-name',
            'description': 'new-description'
        }))
        s_id = json.loads(result.data)['data']['subnetId']
        tools.eq_(s_id, subnet_id)

        subnet = subnet_model.get(subnet_id)
        tools.eq_(subnet['name'], 'new-name')
        tools.eq_(subnet['description'], 'new-description')
