import json
from copy import copy
import env  # noqa
from mock import patch
from nose import tools
import patches
from densefog.common import utils
from densefog.common.utils import MockObject
from icebox.model.project import project as project_model
from icebox.model.project import error as project_error
from icebox.model.iaas import volume as volume_model
from icebox.model.iaas import eip as eip_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import key_pair as key_pair_model
from densefog.model.job import job as job_model

import fixtures
import fixtures_openstack as op_fixtures

project_id_1 = 'prjct-1234'
valid_volume_type = volume_model.SUPPORTED_VOLUME_TYPES[0]
rand_id = 'some-unimportant-id'


def _insert_instance_pre():
    fixtures.insert_instance_type(project_id=project_id_1, instance_type_id=rand_id)  # noqa
    fixtures.insert_image(project_id=project_id_1, image_id=rand_id)
    network_id = fixtures.insert_network(project_id=project_id_1, network_id=rand_id)   # noqa
    fixtures.insert_subnet(project_id=project_id_1, subnet_id=rand_id, network_id=network_id)  # noqa
    fixtures.insert_key_pair(project_id=project_id_1, key_pair_id=rand_id)


def delete_instance(instance_id):
    instance_model.delete(
        project_id=project_id_1,
        instance_ids=[instance_id])


def _create_instance():
    job_id = instance_model.create(
        project_id=project_id_1,
        name='name_a',
        count=1,
        image_id=rand_id,
        instance_type_id=rand_id,
        login_mode='password',
        key_pair_id=None,
        login_password='s3critPassword',
        subnet_id=rand_id,
        user_data="")

    return job_model.get_resources(job_id)[0]


def _create_eip():
    eip_ids = eip_model.create(
        project_id=project_id_1,
        name='name_a',
        count=1)

    return eip_ids[0]


def _delete_eip(eip_id):
    eip_model.delete(
        project_id=project_id_1,
        eip_ids=[eip_id])


def _create_network():
    job_id = network_model.create(
        project_id=project_id_1,
        name='name_a',
        description='desc_a')

    return job_model.get_resources(job_id)[0]


def _delete_network(network_id):
    network_model.delete(
        project_id=project_id_1,
        network_ids=[network_id])


def _create_volume(size=1):
    job_id = volume_model.create(
        project_id=project_id_1,
        size=size,
        name='name_a',
        volume_type=valid_volume_type,
        count=1)

    return job_model.get_resources(job_id)[0]


def _delete_volume(volume_id):
    volume_model.delete(
        project_id=project_id_1,
        volume_ids=[volume_id])


def _create_key_pair():
    id, key = key_pair_model.create(
        project_id=project_id_1,
        name='name_a')

    return id


def _delete_key_pair(key_pair_id):
    key_pair_model.delete(
        project_id=project_id_1,
        key_pair_ids=[key_pair_id])


def mock_nope(*args, **kwargs):
    return True


def mock_create_project(*args, **kwargs):
    server = MockObject(**copy(op_fixtures.op_mock_project))
    server.id = utils.generate_key(32)
    return server


def mock_find_role(*args, **kwargs):
    role = MockObject(**copy(op_fixtures.op_mock_role))
    return role


def mock_find_user(*args, **kwargs):
    user = MockObject(**copy(op_fixtures.op_mock_user))
    return user


def mock_op_quota(*args, **kwargs):
    return copy(op_fixtures.op_mock_update_quota)


def mock_server_create(*args, **kwargs):
    server = MockObject(**copy(op_fixtures.op_mock_server))
    server.id = utils.generate_uuid()
    return server


def mock_port_create(*args, **kwargs):
    port = MockObject(**copy(op_fixtures.op_mock_port))
    return port


def mock_port_show(*args, **kwargs):
    port = MockObject(**copy(op_fixtures.op_mock_port))
    port['port']['status'] = 'available'
    return port


def mock_create_floatingip(*args, **kwargs):
    return op_fixtures.op_mock_create_floatingip['floatingip']


def mock_volume_create(*args, **kwargs):
    volume = MockObject(**copy(op_fixtures.op_mock_volume))
    volume.id = utils.generate_uuid()
    return volume


def mock_volume_get(*args, **kwargs):
    volume = MockObject(**copy(op_fixtures.op_mock_volume))
    volume.id = utils.generate_uuid()
    volume.status = 'available'
    return volume


def mock_create_router(*args, **kwargs):
    mocked = copy(op_fixtures.op_mock_create_router)
    mocked['router']['id'] = utils.generate_uuid()
    return mocked['router']


def mock_create_network(*args, **kwargs):
    mocked = copy(op_fixtures.op_mock_create_network)
    mocked['network']['id'] = utils.generate_uuid()
    return mocked['network']


def mock_create_key_pair(*args, **kwargs):
    return op_fixtures.op_mock_key_pair


@patch('densefog.model.base.ResourceModel.must_not_busy', mock_nope)
@patch('icebox.model.iaas.instance.Instance.status_deletable', mock_nope)
@patch('icebox.model.iaas.volume.Volume.status_deletable', mock_nope)
@patch('icebox.model.iaas.network.Network.status_deletable', mock_nope)
class TestModel:

    def setup(self):
        env.reset_db()
        _insert_instance_pre()

    @patch('icebox.model.iaas.openstack.api.do_interface_detach', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_delete_port', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_stop_server', mock_nope)
    def test_qt_instances(self):
        fixtures.insert_project(project_id_1, qt_instances=2)

        id_a = _create_instance()
        _create_instance()

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_instances'], 2)

        with tools.assert_raises(project_error.ResourceQuotaNotEnough):
            _create_instance()

        delete_instance(id_a)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_instances'], 1)

    @patch('icebox.model.iaas.openstack.api.do_interface_detach', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_delete_port', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_stop_server', mock_nope)
    def test_qt_vcpus(self):
        fixtures.insert_project(project_id_1, qt_vcpus=2)

        id_a = _create_instance()
        _create_instance()

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_vcpus'], 2)

        with tools.assert_raises(project_error.ResourceQuotaNotEnough):
            _create_instance()

        delete_instance(id_a)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_vcpus'], 1)

    @patch('icebox.model.iaas.openstack.api.do_interface_detach', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_delete_port', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_stop_server', mock_nope)
    def test_qt_memory(self):
        fixtures.insert_project(project_id_1, qt_memory=2 * 1024)

        id_a = _create_instance()
        _create_instance()

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_memory'], 2 * 1024)

        with tools.assert_raises(project_error.ResourceQuotaNotEnough):
            _create_instance()

        delete_instance(id_a)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_memory'], 1 * 1024)

    def test_qt_images(self):
        pass

    @patch('icebox.model.iaas.openstack.api.do_create_floatingip', mock_create_floatingip)  # noqa
    def test_qt_eips(self):
        fixtures.insert_project(project_id_1, qt_eips=2)

        fixtures.insert_floatingips()

        id_a = _create_eip()
        _create_eip()

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_eips'], 2)

        with tools.assert_raises(project_error.ResourceQuotaNotEnough):
            _create_eip()

        _delete_eip(id_a)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_eips'], 1)

    @patch('icebox.model.iaas.openstack.api.do_create_router', mock_create_router)            # noqa
    @patch('icebox.model.iaas.openstack.api.do_create_network', mock_create_network)          # noqa
    def test_qt_networks(self):
        fixtures.insert_project(project_id_1, qt_networks=2)

        id_a = _create_network()
        _create_network()

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_networks'], 2)

        with tools.assert_raises(project_error.ResourceQuotaNotEnough):
            _create_network()

        _delete_network(id_a)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_networks'], 1)

    @patch('icebox.model.iaas.openstack.api.do_create_data_volume', mock_volume_create)  # noqa
    def test_qt_volumes(self):
        fixtures.insert_project(project_id_1, qt_volumes=2)

        id_a = _create_volume()
        _create_volume()

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_volumes'], 2)

        with tools.assert_raises(project_error.ResourceQuotaNotEnough):
            _create_volume()

        _delete_volume(id_a)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_volumes'], 1)

    @patch('icebox.model.iaas.openstack.api.do_create_data_volume', mock_volume_create)  # noqa
    def test_qt_volume_size(self):
        fixtures.insert_project(project_id_1, qt_volume_size=100)

        id_a = _create_volume(size=50)
        _create_volume(size=50)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_volume_size'], 100)

        with tools.assert_raises(project_error.ResourceQuotaNotEnough):
            _create_volume(size=1)

        _delete_volume(id_a)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_volume_size'], 50)

    @patch('icebox.model.iaas.openstack.api.do_create_keypair', mock_create_key_pair)  # noqa
    def test_qt_key_pairs(self):
        fixtures.insert_project(project_id_1, qt_key_pairs=2)

        id_a = _create_key_pair()
        _create_key_pair()

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_key_pairs'], 2)

        with tools.assert_raises(project_error.ResourceQuotaNotEnough):
            _create_key_pair()

        _delete_key_pair(id_a)

        project = project_model.get(project_id_1)
        tools.eq_(project['cu_key_pairs'], 1)


@patch('densefog.model.base.ResourceModel.must_not_busy', mock_nope)
@patch('icebox.model.iaas.instance.Instance.status_deletable', mock_nope)
@patch('icebox.model.iaas.volume.Volume.status_deletable', mock_nope)
@patch('icebox.model.iaas.network.Network.status_deletable', mock_nope)
@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        _insert_instance_pre()

    @patch('icebox.model.iaas.openstack.api.do_create_data_volume', mock_volume_create)  # noqa
    def test_describe_quotas(self):
        fixtures.insert_project(project_id_1,
                                qt_instances=100,
                                qt_memory=100 * 1024,
                                qt_volumes=100,
                                qt_volume_size=100 * 1024)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'CreateInstances',
            'instanceTypeId': rand_id,
            'imageId': rand_id,
            'subnetId': rand_id,
            'loginMode': 'keyPair',
            'keyPairId': rand_id,
            'count': 10
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'CreateVolumes',
            'size': 1,
            'volumeType': valid_volume_type,
            'count': 10
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeQuotas'
        }))

        tools.eq_(0, json.loads(result.data)['retCode'])

        data = json.loads(result.data)
        tools.eq_(100, data['data']['total']['instances'])
        tools.eq_(100 * 1024, data['data']['total']['memory'])
        tools.eq_(100, data['data']['total']['volumes'])

        tools.eq_(10, data['data']['usage']['instances'])
        tools.eq_(10 * 1024, data['data']['usage']['memory'])
        tools.eq_(10, data['data']['usage']['volumes'])

    def test_qt_instances(self):
        fixtures.insert_project(project_id_1, qt_instances=2)

        def send_request(count):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'CreateInstances',
                'instanceTypeId': rand_id,
                'imageId': rand_id,
                'subnetId': rand_id,
                'loginMode': 'keyPair',
                'keyPairId': rand_id,
                'count': count
            }))

            return result

        result = send_request(2)
        tools.eq_(0, json.loads(result.data)['retCode'])

        result = send_request(1)

        data = json.loads(result.data)
        tools.eq_(data['retCode'], 4113)
        tools.eq_(data['message'],
                  'Project quota[instances] not enough: want [1], but have [0]')  # noqa
        tools.eq_(data['data']['quota'], 2)
        tools.eq_(data['data']['used'], 2)
        tools.eq_(data['data']['want'], 1)
