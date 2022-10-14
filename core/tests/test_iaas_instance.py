import env  # noqa
import json
import datetime
import patches
import copy
from mock import patch
from nose import tools
from densefog.common import utils
from densefog.common.utils import MockObject
from densefog.model.job import job as job_model
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import key_pair as key_pair_model
from icebox.model.iaas import image as image_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import eip as eip_model
from icebox.model.iaas.openstack import compute

import fixtures

project_id_1 = 'prjct-1234'
exc = Exception('HTTP Connection error')


def mock_server_create(*args, **kwargs):
    server = MockObject(**fixtures.op_mock_server)
    server.id = utils.generate_key(36)
    return server


def mock_port_create(*args, **kwargs):
    port = copy.copy(fixtures.op_mock_port)
    return port


def mock_port_show(*args, **kwargs):
    port = copy.copy(fixtures.op_mock_port)
    port['status'] = 'available'
    return port


def mock_volume_create(*args, **kwargs):
    volume = MockObject(**fixtures.op_mock_volume)
    volume.id = utils.generate_key(36)
    return volume


def mock_volume_get(*args, **kwargs):
    volume = MockObject(**fixtures.op_mock_volume)
    volume.id = utils.generate_key(36)
    volume.status = 'available'
    return volume


def mock_create_floatingip(*args, **kwargs):
    return fixtures.op_mock_create_floatingip


def mock_nope(*args, **kwargs):
    return True


def _reset_state(instance_id, status):
    instance_model.Instance.update(instance_id, status=status)


class TestModel:
    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

        self.instance_type_id = fixtures.insert_instance_type()
        self.image_id = fixtures.insert_image()

        fixtures.insert_network(status=network_model.NETWORK_STATUS_ACTIVE)
        self.subnet_id = fixtures.insert_subnet()

    def test_create(self):  # noqa
        instance_model.create(
            project_id=project_id_1,
            name='name',
            count=2,
            image_id=self.image_id,
            instance_type_id=self.instance_type_id,
            login_mode='password',
            key_pair_id=None,
            login_password='s3critPassword',
            subnet_id=self.subnet_id,
            user_data="")

        # create success
        tools.eq_(instance_model.limitation()['total'], 2)

        # WatchingJobs run_at is 2 seconds later
        # so set run_at here, so that limitation can find it.
        run_at = datetime.datetime.now() + datetime.timedelta(seconds=2)
        jobs = job_model.limitation(run_at=run_at)['items']

        job_actions = [j['action'] for j in jobs]
        # there are three jobs in table. 2 CreateServer, 1 WatchingJobs.
        tools.eq_(len(job_actions), 3)
        tools.eq_(set(job_actions), set(['WatchingJobs', 'CreateServer']))

    def test_create_by_login_mode(self):
        key_pair_id = fixtures.insert_key_pair()

        def create_by_login_mode(login_mode, key_pair_id, login_password):
            instance_model.create(
                project_id=project_id_1,
                name='inst-name',
                count=1,
                image_id=self.image_id,
                instance_type_id=self.instance_type_id,
                subnet_id=self.subnet_id,
                # login_mode
                login_mode=login_mode,
                key_pair_id=key_pair_id,
                login_password=login_password,
                user_data="")

        with tools.assert_raises(iaas_error.InstanceLoginModeError):
            create_by_login_mode('keyPair', None, 's3critPassword')

        with tools.assert_raises(iaas_error.InstanceLoginModeError):
            create_by_login_mode('password', key_pair_id, None)

        with tools.assert_raises(iaas_error.InstanceLoginModeError):
            create_by_login_mode(None, key_pair_id, 's3critPassword')

        create_by_login_mode('keyPair', key_pair_id, None)
        create_by_login_mode('password', None, 's3critPassword')

        tools.eq_(instance_model.limitation()['total'], 2)
        # 2 creating jobs, 2 watching jobs.
        tools.eq_(job_model.limitation()['total'], 4)

    def test_create_by_name(self):
        def create_by_name(name):
            instance_model.create(
                project_id=project_id_1,
                count=1,
                login_mode='password',
                key_pair_id=None,
                login_password='s3critPassword',
                image_id=self.image_id,
                instance_type_id=self.instance_type_id,
                subnet_id=self.subnet_id,
                # name
                name=name,
                user_data="")

        with tools.assert_raises(iaas_error.InstanceNameTooComplex):
            create_by_name('name.com')

        with tools.assert_raises(iaas_error.InstanceNameTooComplex):
            create_by_name('name@com')

        with tools.assert_raises(iaas_error.InstanceNameTooComplex):
            create_by_name('name*com')

        create_by_name('name-com_1')
        create_by_name('name-com_2')

    def test_create_by_ip(self):
        def create_by_ip(ip):
            instance_model.create(
                project_id=project_id_1,
                name='some-instance',
                count=1,
                login_mode='password',
                key_pair_id=None,
                login_password='s3critPassword',
                image_id=self.image_id,
                instance_type_id=self.instance_type_id,
                subnet_id=self.subnet_id,
                # ip
                ip_address=ip,
                user_data="")

        with tools.assert_raises(iaas_error.CreateInstanceWhenIpAddressNotValid):  # noqa
            create_by_ip('192.168.100.1')

        with tools.assert_raises(iaas_error.CreateInstanceWhenIpAddressNotValid):  # noqa
            create_by_ip('192.168.200.1')

        with tools.assert_raises(iaas_error.CreateInstanceWhenIpAddressNotValid):  # noqa
            create_by_ip('192.168.300.1')

        create_by_ip('192.168.0.1')

    @patch('icebox.model.iaas.openstack.api.do_create_boot_volume')
    @patch('icebox.model.iaas.waiter.wait_volume_available')
    @patch('icebox.model.iaas.openstack.api.do_create_port')
    @patch('icebox.model.iaas.waiter.wait_port_available')
    @patch('icebox.model.iaas.openstack.api.do_create_server')
    @patch('icebox.model.iaas.waiter.wait_server_available')
    def test_create_server(self, server_wait, server_create,
                           port_wait, port_create,
                           volume_wait, volume_create):
        mock0 = MockObject(**copy.copy(fixtures.op_mock_volume))
        mock0.id = utils.generate_key(36)
        volume_create.return_value = mock0

        volume_wait.return_value = mock0

        mock2 = MockObject(**copy.copy(fixtures.op_mock_port))
        mock2.id = utils.generate_key(36)
        port_create.return_value = mock2

        port_wait.return_value = mock2

        mock3 = MockObject(**copy.copy(fixtures.op_mock_server))
        mock3.id = utils.generate_key(36)
        server_create.return_value = mock3

        server_wait.return_value = mock3

        fixtures.insert_instance(project_id_1, 'instance_id_a')
        fixtures.insert_key_pair(key_pair_id='key-a')

        instance = instance_model.create_server('instance_id_a', 'key-a',
                                                '192.168.0.1',
                                                's3critPassword', '')

        tools.eq_(instance['op_volume_id'], mock0['id'])
        tools.eq_(instance['address'], mock2['fixed_ips'][0]['ip_address'])
        tools.eq_(instance['op_port_id'], mock2['id'])
        tools.eq_(instance['op_server_id'], mock3['id'])
        tools.eq_(instance['key_pair_id'], 'key-a')

    @patch('icebox.model.iaas.openstack.api.do_interface_detach', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_delete_port', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_stop_server', mock_nope)
    def test_delete(self):
        instance_id = fixtures.insert_instance(project_id_1, 'instance_id_a')
        project_id = fixtures.insert_project('project_id_2')

        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            instance_model.delete(project_id, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        instance_model.delete(project_id_1, [instance_id])

        tools.eq_(instance_model.get(instance_id)['status'],
                  instance_model.INSTANCE_STATUS_DELETED)

    def test_delete_with_status(self):
        fixtures.insert_instance(
            project_id_1,
            instance_id='instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPING)

        with tools.assert_raises(iaas_error.ResourceIsBusy):
            instance_model.delete(project_id_1, ['instance_id_a'])

        fixtures.insert_instance(
            project_id_1,
            instance_id='instance_id_b',
            status=instance_model.INSTANCE_STATUS_DELETED)

        with tools.assert_raises(iaas_error.InstanceCanNotDelete):
            instance_model.delete(project_id_1, ['instance_id_b'])

    def test_delete_with_volume_attached(self):
        fixtures.insert_instance(
            project_id_1,
            instance_id='instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_volume(project_id_1, volume_id='volume_id_a')
        fixtures.insert_instance_volume(
            project_id_1,
            instance_id='instance_id_a',
            volume_id='volume_id_a')
        with tools.assert_raises(iaas_error.DeleteInstanceWhenVolumesAttaching):  # noqa
            instance_model.delete(project_id_1, ['instance_id_a'])

    def test_delete_with_eip_associated(self):
        fixtures.insert_instance(
            project_id_1,
            instance_id='instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_eip(project_id=project_id_1, eip_id='eip_id_a')
        fixtures.insert_eip_resource(resource_type=eip_model.RESOURCE_TYPE_INSTANCE,  # noqa
                                     resource_id='instance_id_a',
                                     eip_id='eip_id_a')

        with tools.assert_raises(iaas_error.DeleteInstanceWhenEipAssociating):
            instance_model.delete(project_id_1, ['instance_id_a'])

    @patch('icebox.model.iaas.openstack.api.do_start_server', mock_nope)  # noqa
    def test_start(self):
        instance_id = fixtures.insert_instance(project_id_1, 'instance_id_a')
        project_id = fixtures.insert_project('project_id_2')

        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            instance_model.start(project_id, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_PENDING)
        with tools.assert_raises(iaas_error.ResourceIsBusy):
            instance_model.start(project_id_1, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        with tools.assert_raises(iaas_error.InstanceCanNotStart):
            instance_model.start(project_id_1, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_STOPPED)
        instance_model.start(project_id_1, [instance_id])

        tools.eq_(instance_model.get(instance_id)['status'],
                  instance_model.INSTANCE_STATUS_STARTING)
        tools.eq_(job_model.limitation()['total'], 1)

    @patch('icebox.model.iaas.openstack.api.do_stop_server', mock_nope)
    def test_stop(self):
        instance_id = fixtures.insert_instance(project_id_1, 'instance_id_a')
        project_id = fixtures.insert_project('project_id_2')

        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            instance_model.stop(project_id, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_PENDING)
        with tools.assert_raises(iaas_error.ResourceIsBusy):
            instance_model.stop(project_id_1, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_STOPPED)
        with tools.assert_raises(iaas_error.InstanceCanNotStop):
            instance_model.stop(project_id_1, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        instance_model.stop(project_id_1, [instance_id])

        tools.eq_(instance_model.get(instance_id)['status'],
                  instance_model.INSTANCE_STATUS_STOPPING)
        tools.eq_(job_model.limitation()['total'], 1)

    @patch('icebox.model.iaas.openstack.api.do_reboot_server', mock_nope)
    def test_restart(self):
        instance_id = fixtures.insert_instance(project_id_1, 'instance_id_a')
        project_id = fixtures.insert_project('project_id_2')

        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            instance_model.restart(project_id, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_PENDING)
        with tools.assert_raises(iaas_error.ResourceIsBusy):
            instance_model.restart(project_id_1, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_ERROR)
        with tools.assert_raises(iaas_error.InstanceCanNotRestart):
            instance_model.restart(project_id_1, [instance_id])

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        instance_model.restart(project_id_1, [instance_id])

        tools.eq_(instance_model.get(instance_id)['status'],
                  instance_model.INSTANCE_STATUS_RESTARTING)
        tools.eq_(job_model.limitation()['total'], 1)

    def test_reset(self):
        fixtures.insert_image(project_id=project_id_1, image_id='img-reset')
        fixtures.insert_instance(project_id=project_id_1,
                                 instance_id='instance_id_a')

        project_id = fixtures.insert_project('project_id_2')
        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            instance_model.reset(project_id, ['instance_id_a'],
                                 'password', None, 's3critPassword')

        fixtures.insert_instance(project_id=project_id_1,
                                 instance_id='instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_PENDING)
        with tools.assert_raises(iaas_error.ResourceIsBusy):
            instance_model.reset(project_id_1, ['instance_id_b'],
                                 'password', None, 's3critPassword')

        fixtures.insert_instance(project_id=project_id_1,
                                 instance_id='instance_id_c',
                                 status=instance_model.INSTANCE_STATUS_STOPPED)
        # set boot volume to empty
        instance_model.Instance.update('instance_id_c', op_volume_id='')
        with tools.assert_raises(iaas_error.InstanceResetUnsupported):
            instance_model.reset(project_id_1, ['instance_id_c'],
                                 'password', None, 's3critPassword')

        fixtures.insert_instance(project_id=project_id_1,
                                 instance_id='instance_id_d',
                                 status=instance_model.INSTANCE_STATUS_STOPPED)
        instance_model.reset(project_id_1, ['instance_id_d'],
                             'password', None, 's3critPassword')

        tools.eq_(instance_model.get('instance_id_d')['status'],
                  instance_model.INSTANCE_STATUS_SCHEDULING)
        # 1 reseting job, 1 watching job.
        tools.eq_(job_model.limitation()['total'], 2)

    @patch('icebox.model.iaas.openstack.api.do_change_password', mock_nope)  # noqa
    def test_change_password(self):
        fixtures.insert_instance(project_id_1, instance_id='instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)  # noqa
        fixtures.insert_instance(project_id_1, instance_id='instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_STOPPED)

        with tools.assert_raises(iaas_error.InstanceLoginPasswordWeak):
            instance_model.change_password(project_id_1, 'instance_id_a', '123456')  # noqa

        with tools.assert_raises(iaas_error.InstanceCanNotChangePassword):
            instance_model.change_password(project_id_1, 'instance_id_b', 's3critPassword')  # noqa

        instance_model.change_password(project_id_1, 'instance_id_a', 's3critPassword')  # noqa

    @patch('icebox.model.iaas.openstack.api.do_change_keypair', mock_nope)  # noqa
    def test_change_key_pair(self):
        fixtures.insert_instance(project_id_1, instance_id='instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)  # noqa
        fixtures.insert_instance(project_id_1, instance_id='instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_STOPPED)

        fixtures.insert_key_pair(key_pair_id='key-a')
        fixtures.insert_key_pair(key_pair_id='key-b',
                                 status=key_pair_model.KEY_PAIR_STATUS_DELETED)

        with tools.assert_raises(iaas_error.KeyPairNotFound):
            instance_model.change_key_pair(project_id_1, 'instance_id_a', 'key-c')  # noqa

        with tools.assert_raises(iaas_error.ResourceIsDeleted):
            instance_model.change_key_pair(project_id_1, 'instance_id_a', 'key-b')  # noqa

        with tools.assert_raises(iaas_error.InstanceCanNotChangeKeyPair):
            instance_model.change_key_pair(project_id_1, 'instance_id_b', 'key-a')  # noqa

        instance_model.change_key_pair(project_id_1, 'instance_id_a', 'key-a')

    def test_reset_with_deleted_image(self):
        fixtures.insert_image(project_id=project_id_1,
                              image_id='img-reset',
                              status=image_model.IMAGE_STATUS_DELETED)
        fixtures.insert_instance(
            project_id=project_id_1,
            instance_id='instance_id_a',
            image_id='img-reset',
            status=instance_model.INSTANCE_STATUS_STOPPED)

        # use self image, but the image has been delete.
        # so reset will raise exception
        with tools.assert_raises(iaas_error.ResetInstanceWithIllegalImage):
            instance_model.reset(project_id_1, ['instance_id_a'],
                                 'password', None, 's3critPassword')

    def test_reset_with_other_image(self):
        fixtures.insert_image(project_id=project_id_1, image_id='img-reset')
        fixtures.insert_instance(
            project_id=project_id_1,
            instance_id='instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPED)

        # some unexist image
        with tools.assert_raises(iaas_error.ImageNotFound):
            instance_model.reset(project_id_1, ['instance_id_a'],
                                 'password', None, 's3critPassword',
                                 image_id='some-non-exist-image')

        # another image
        fixtures.insert_image(project_id=project_id_1,
                              image_id='new-image-id')
        # reset to another image
        instance_model.reset(project_id_1, ['instance_id_a'],
                             'password', None, 's3critPassword',
                             image_id='new-image-id')

        tools.eq_(instance_model.get('instance_id_a')['image_id'],
                  'new-image-id')
        tools.eq_(instance_model.get('instance_id_a')['status'],
                  instance_model.INSTANCE_STATUS_SCHEDULING)
        # 1 for reseting, 1 for watching job.
        tools.eq_(job_model.limitation()['total'], 2)

    def test_reset_by_login_mode(self):
        fixtures.insert_image(image_id='img-reset')
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPED)

        with tools.assert_raises(iaas_error.InstanceLoginModeError):
            instance_model.reset(project_id_1, [instance_id],
                                 'password', 'key-pair-id-123', None)

        with tools.assert_raises(iaas_error.InstanceLoginModeError):
            instance_model.reset(project_id_1, [instance_id],
                                 'keyPair', None, 's3critPassword')

        with tools.assert_raises(iaas_error.InstanceLoginModeError):
            instance_model.reset(project_id_1, [instance_id],
                                 None, 'key-pair-id-123', 's3critPassword')

    @patch('icebox.model.iaas.openstack.api.do_resize_server', mock_nope)
    def test_resize(self):
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPED)

        instance_type_id = fixtures.insert_instance_type(
            instance_type_id='itp-resize')

        instance_model.resize(project_id_1,
                              [instance_id],
                              instance_type_id)

        tools.eq_(instance_model.get(instance_id)['status'],
                  instance_model.INSTANCE_STATUS_SCHEDULING)

        tools.eq_(job_model.limitation()['total'], 1)

    def test_resize_with_exceptions(self):
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPED)

        instance_type_id = fixtures.insert_instance_type(
            instance_type_id='itp-resize')
        project_id = fixtures.insert_project('project_id_2')

        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            instance_model.resize(project_id,
                                  [instance_id],
                                  instance_type_id)

        _reset_state(instance_id, instance_model.INSTANCE_STATUS_PENDING)
        with tools.assert_raises(iaas_error.InstanceCanNotResize):
            instance_model.resize(project_id_1,
                                  [instance_id],
                                  instance_type_id)

        _reset_state(instance_id, instance_model.INSTANCE_STATUS_STOPPED)
        # set boot volume to empty
        instance_model.Instance.update(instance_id, op_volume_id='')
        with tools.assert_raises(iaas_error.InstanceResizeUnsupported):
            instance_model.resize(project_id_1,
                                  [instance_id],
                                  instance_type_id)

    def test_sync(self):
        instance_id = fixtures.insert_instance(project_id_1, 'instance_id_a')

        mock = MockObject(**fixtures.op_mock_server)
        mock.task_state = compute.SERVER_TASK_STATE_SPAWNING
        with patch('icebox.model.iaas.openstack.api.do_get_server', return_value=mock):    # noqa
            instance = instance_model.sync(instance_id)
            tools.eq_(instance['status'],
                      instance_model.INSTANCE_STATUS_PENDING)

        mock = MockObject(**fixtures.op_mock_server)
        mock.power_state = compute.SERVER_POWER_STATE_SHUTDOWN
        with patch('icebox.model.iaas.openstack.api.do_get_server', return_value=mock):     # noqa
            instance = instance_model.sync(instance_id)
            tools.eq_(instance['status'],
                      instance_model.INSTANCE_STATUS_STOPPED)

        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_DELETED)
        with patch('icebox.model.iaas.openstack.api.do_get_server', return_value=mock):     # noqa
            instance = instance_model.sync(instance_id)
            tools.eq_(instance['status'],
                      instance_model.INSTANCE_STATUS_DELETED)


class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

        self.instance_type_id = fixtures.insert_instance_type()
        self.image_id = fixtures.insert_image()
        self.network_id = fixtures.insert_network(
            status=network_model.NETWORK_STATUS_ACTIVE)
        self.subnet_id = fixtures.insert_subnet()

    @patches.check_access_key(project_id_1)
    def test_describe_instances(self):
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)

        def send_request(verbose):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeInstances',
                'verbose': verbose
            }))
            return result

        result = send_request(False)
        data = json.loads(result.data)

        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])

        instance = data['data']['instanceSet'][0]

        tools.eq_(instance_id, instance['instanceId'])

        tools.eq_(None, instance['eipId'])
        with tools.assert_raises(KeyError):
            tools.ok_(instance['eip'])

        tools.eq_(0, len(instance['volumeIds']))
        with tools.assert_raises(KeyError):
            tools.ok_(instance['volumes'])

        eip_id = fixtures.insert_eip(project_id=project_id_1)
        fixtures.insert_eip_resource(project_id_1,
                                     eip_id=eip_id,
                                     resource_id=instance_id)

        volume_id = fixtures.insert_volume(project_id=project_id_1)
        fixtures.insert_instance_volume(project_id_1,
                                        volume_id=volume_id,
                                        instance_id=instance_id)

        result = send_request(True)
        data = json.loads(result.data)

        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])

        instance = data['data']['instanceSet'][0]

        tools.eq_(instance_id, instance['instanceId'])

        tools.eq_(eip_id, instance['eipId'])
        tools.assert_not_equal(None, instance['eip'])

        tools.eq_(volume_id, instance['volumeIds'][0])
        tools.assert_not_equal(None, instance['volumes'][0])

        tools.eq_(self.instance_type_id, instance['instanceTypeId'])
        tools.assert_not_equal(None, instance['instanceType'])

        tools.eq_(self.image_id, instance['imageId'])
        tools.assert_not_equal(None, instance['image'])

        tools.eq_(self.network_id, instance['networkId'])
        tools.assert_not_equal(None, instance['network'])

        tools.eq_(self.subnet_id, instance['subnetId'])
        tools.assert_not_equal(None, instance['subnet'])

    @patches.check_access_key(project_id_1)
    def test_describe_instances_with_status(self):
        fixtures.insert_instance(
            project_id_1, 'inst-aaa',
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_instance(
            project_id_1, 'inst-bbb',
            status=instance_model.INSTANCE_STATUS_DELETED)
        fixtures.insert_instance(
            project_id_1, 'inst-ccc',
            status=instance_model.INSTANCE_STATUS_PENDING)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeInstances',
                'status': status
            }))
            return result

        result = send_request([instance_model.INSTANCE_STATUS_ACTIVE,
                               instance_model.INSTANCE_STATUS_PENDING])

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.instances.InstanceBiller.create_instances', mock_nope)  # noqa
    def test_create_instances(self):
        key_pair_id = fixtures.insert_key_pair()

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'CreateInstances',
                'instanceTypeId': self.instance_type_id,
                'imageId': self.image_id,
                'subnetId': self.subnet_id,
                'loginMode': 'keyPair',
                'keyPairId': key_pair_id
            }))
            return result

        result = send_request()
        tools.eq_(0, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.instances.InstanceBiller.create_instances', mock_nope)  # noqa
    def test_create_instances_by_login_mode(self):
        key_pair_id = fixtures.insert_key_pair()

        def send_request(login_mode, key_pair_id, login_password):
            spec = {
                'action': 'CreateInstances',
                'instanceTypeId': self.instance_type_id,
                'imageId': self.image_id,
                'subnetId': self.subnet_id,
                'loginMode': login_mode
            }
            if key_pair_id:
                spec.update({'keyPairId': key_pair_id})

            if login_password:
                spec.update({'loginPassword': login_password})

            result = fixtures.public.post('/', data=json.dumps(spec))
            return result

        result = send_request('keyPair', None, 's3cr1tpasswd')
        tools.eq_(4100, json.loads(result.data)['retCode'])

        result = send_request('password', key_pair_id, None)
        tools.eq_(4100, json.loads(result.data)['retCode'])

        result = send_request('keyPair', key_pair_id, None)
        tools.eq_(0, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.instances.InstanceBiller.create_instances', mock_nope)  # noqa
    def test_create_instances_by_ip(self):
        def send_request(ip_address, count):
            spec = {
                'action': 'CreateInstances',
                'instanceTypeId': self.instance_type_id,
                'imageId': self.image_id,
                'subnetId': self.subnet_id,
                'loginMode': 'password',
                'loginPassword': 's3critPassword',
                'ipAddress': ip_address,
                'count': count,
            }

            result = fixtures.public.post('/', data=json.dumps(spec))
            return result

        # ip is invalid
        result = send_request('192.168.300.1', 1)
        tools.eq_(4714, json.loads(result.data)['retCode'])

        # count is larger than 1.
        result = send_request('192.168.0.1', 2)
        tools.eq_(4714, json.loads(result.data)['retCode'])

        # ok.
        result = send_request('192.168.0.1', 1)
        tools.eq_(0, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_start_server', mock_nope)
    def test_start_instances(self):
        fixtures.insert_instance(project_id_1, 'instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_STOPPED)

        def send_request(instance_id):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'StartInstances',
                'instanceIds': [instance_id]
            }))
            return result

        with patch('icebox.model.iaas.openstack.api.do_start_server',
                   side_effect=iaas_error.ProviderStartServerError('ex', 'stack')):  # noqa
            result = send_request('instance_id_a')
            tools.eq_(5001, json.loads(result.data)['retCode'])

        result = send_request('instance_id_a')
        instance = instance_model.get('instance_id_a')
        tools.eq_(instance['status'], instance_model.INSTANCE_STATUS_STARTING)

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_change_password', mock_nope)  # noqa
    def test_instance_change_password(self):
        fixtures.insert_instance(project_id_1, instance_id='instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_instance(project_id_1, instance_id='instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_STOPPED)

        def send_request(instance_id, password):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'ChangePassword',
                'instanceId': instance_id,
                'loginPassword': password,
            }))
            return result

        with patch('icebox.model.iaas.openstack.api.do_change_password',
                   side_effect=iaas_error.ProviderChangePasswordError('ex', 'stack')):  # noqa
            result = send_request('instance_id_a', 's3critPassword')
            tools.eq_(5001, json.loads(result.data)['retCode'])

        # can not change password for stopped instance.
        result = send_request('instance_id_b', 's3critPassword')
        tools.eq_(4105, json.loads(result.data)['retCode'])

        # password should strong
        result = send_request('instance_id_a', 'simplepass')
        tools.eq_(4100, json.loads(result.data)['retCode'])

        result = send_request('instance_id_a', 's3critPassword')
        tools.eq_(0, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_change_keypair', mock_nope)  # noqa
    def test_instance_change_key_pair(self):
        fixtures.insert_instance(project_id_1, instance_id='instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_instance(project_id_1, instance_id='instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_STOPPED)

        fixtures.insert_key_pair(key_pair_id='key-a')
        fixtures.insert_key_pair(key_pair_id='key-b',
                                 status=key_pair_model.KEY_PAIR_STATUS_DELETED)

        def send_request(instance_id, key_pair_id):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'ChangeKeyPair',
                'instanceId': instance_id,
                'keyPairId': key_pair_id,
            }))
            return result

        with patch('icebox.model.iaas.openstack.api.do_change_keypair',
                   side_effect=iaas_error.ProviderChangeKeyPairError('ex', 'stack')):  # noqa
            result = send_request('instance_id_a', 'key-a')
            tools.eq_(5001, json.loads(result.data)['retCode'])

        # can not change keypair for stopped instance.
        result = send_request('instance_id_b', 'key-a')
        tools.eq_(4105, json.loads(result.data)['retCode'])

        # keypair should active.
        result = send_request('instance_id_a', 'key-b')
        tools.eq_(4105, json.loads(result.data)['retCode'])

        # keypair should exists
        result = send_request('instance_id_a', 'key-c')
        tools.eq_(4104, json.loads(result.data)['retCode'])

        result = send_request('instance_id_a', 'key-a')
        tools.eq_(0, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_stop_server', mock_nope)
    def test_stop_instances(self):
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'StopInstances',
                'instanceIds': [instance_id]
            }))
            return result

        with patch('icebox.model.iaas.openstack.api.do_stop_server',
                   side_effect=iaas_error.ProviderStopServerError('ex', 'stack')):  # noqa
            result = send_request()
            tools.eq_(5001, json.loads(result.data)['retCode'])

        result = send_request()

        instance = instance_model.get(instance_id)
        tools.eq_(instance['status'], instance_model.INSTANCE_STATUS_STOPPING)

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_reboot_server', mock_nope)  # noqa
    def test_restart_instances(self):
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)

        def send_request(restart_type=None):
            data = {
                'action': 'RestartInstances',
                'instanceIds': [instance_id],
            }
            if restart_type:
                data['restartType'] = restart_type

            result = fixtures.public.post('/', data=json.dumps(data))
            return result

        with patch('icebox.model.iaas.openstack.api.do_reboot_server',
                   side_effect=iaas_error.ProviderRebootServerError('ex', 'stack')):  # noqa
            result = send_request()
            tools.eq_(5001, json.loads(result.data)['retCode'])

        # restart with unknown type
        result = send_request('other-type')
        tools.eq_(4110, json.loads(result.data)['retCode'])

        # HARD restart
        result = send_request(instance_model.RESTART_TYPE_HARD)
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(instance_model.get(instance_id)['status'],
                  instance_model.INSTANCE_STATUS_RESTARTING)    # noqa

        # SOFT restart
        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        result = send_request(instance_model.RESTART_TYPE_SOFT)
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(instance_model.get(instance_id)['status'],
                  instance_model.INSTANCE_STATUS_RESTARTING)    # noqa

        # default is SOFT restart
        instance_model.Instance.update(
            instance_id,
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        result = send_request()
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(instance_model.get(instance_id)['status'],
                  instance_model.INSTANCE_STATUS_RESTARTING)    # noqa

    @patches.check_access_key(project_id_1)
    def test_reset_instances(self):
        instance_id = fixtures.insert_instance(
            project_id=project_id_1,
            instance_id='instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPED)

        fixtures.insert_image(image_id='new-image-id',
                              project_id=project_id_1)

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'ResetInstances',
                'instanceIds': [instance_id],
                'loginMode': 'password',
                'loginPassword': 'p1ssw00d',
                'imageId': 'new-image-id',
            }))
            return result

        send_request()

        instance = instance_model.get(instance_id)
        tools.eq_(instance['image_id'], 'new-image-id')
        tools.eq_(instance['status'], instance_model.INSTANCE_STATUS_SCHEDULING)    # noqa

    @patches.check_access_key(project_id_1)
    def test_reset_legacy_instances(self):
        instance_id = fixtures.insert_instance(
            project_id=project_id_1,
            instance_id='instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPED)
        # set boot volume to empty
        instance_model.Instance.update(instance_id, op_volume_id='')

        fixtures.insert_image(image_id='new-image-id',
                              project_id=project_id_1)

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'ResetInstances',
                'instanceIds': [instance_id],
                'loginMode': 'password',
                'loginPassword': 'p1ssw00d',
                'imageId': 'new-image-id',
            }))
            return result

        result = send_request()

        tools.eq_(4106, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    def test_reset_instances_with_deleted_image(self):
        fixtures.insert_image(project_id=project_id_1,
                              image_id='img-reset',
                              status=image_model.IMAGE_STATUS_DELETED)
        fixtures.insert_instance(
            project_id=project_id_1,
            instance_id='instance_id_a',
            image_id='img-reset',
            status=instance_model.INSTANCE_STATUS_STOPPED)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ResetInstances',
            'instanceIds': ['instance_id_a'],
            'loginMode': 'password',
            'loginPassword': 'p1ssw00d'
        }))
        tools.eq_(4751, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_resize_server', mock_nope)
    @patch('icebox.billing.instances.InstanceBiller.resize_instances', mock_nope)  # noqa
    def test_resize_instances(self):
        fixtures.insert_instance_type(instance_type_id='instance_type_id_a')
        fixtures.insert_instance_type(instance_type_id='instance_type_id_b')

        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPED)

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'ResizeInstances',
                'instanceIds': [instance_id],
                'instanceTypeId': 'instance_type_id_b',
            }))
            return result

        with patch('icebox.model.iaas.openstack.api.do_resize_server',
                   side_effect=iaas_error.ProviderResizeServerError('ex', 'stack')):  # noqa
            result = send_request()
            tools.eq_(5001, json.loads(result.data)['retCode'])

        result = send_request()

        instance = instance_model.get(instance_id)
        tools.eq_(instance['instance_type_id'], 'instance_type_id_b')
        tools.eq_(instance['status'], instance_model.INSTANCE_STATUS_SCHEDULING)    # noqa

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.instances.InstanceBiller.resize_instances', mock_nope)  # noqa
    def test_resize_legacy_instances(self):
        fixtures.insert_instance_type(instance_type_id='instance_type_id_a')
        fixtures.insert_instance_type(instance_type_id='instance_type_id_b')
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_STOPPED)
        # set boot volume to empty
        instance_model.Instance.update(instance_id, op_volume_id='')

        fixtures.insert_image(image_id='new-image-id',
                              project_id=project_id_1)

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'ResizeInstances',
                'instanceIds': [instance_id],
                'instanceTypeId': 'instance_type_id_b',
            }))
            return result

        result = send_request()

        tools.eq_(4106, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_interface_detach', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_delete_port', mock_nope)
    @patch('icebox.billing.instances.InstanceBiller.delete_instances', mock_nope)  # noqa
    def test_delete_instances(self):
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DeleteInstances',
                'instanceIds': [instance_id]
            }))
            return result

        result = send_request()
        instance_ids = json.loads(result.data)['data']['instanceIds']
        tools.eq_(len(instance_ids), 1)
        tools.eq_(instance_ids[0], instance_id)

        instance = instance_model.get(instance_id)
        tools.eq_(instance['status'], instance_model.INSTANCE_STATUS_DELETED)

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_interface_detach', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_delete_port', mock_nope)
    @patch('icebox.billing.instances.InstanceBiller.delete_instances', mock_nope)  # noqa
    def test_delete_instances_with_provider_error(self):
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DeleteInstances',
                'instanceIds': [instance_id]
            }))
            return result

        # delete port should not fail
        with patch('icebox.model.iaas.openstack.api.do_delete_port',
                   side_effect=iaas_error.ProviderDeletePortError('ex', 'stack')):  # noqa
            result = send_request()
            tools.eq_(5001, json.loads(result.data)['retCode'])

        # detach interface can fail
        with patch('icebox.model.iaas.openstack.api.do_interface_detach',
                   side_effect=iaas_error.ProviderInterfaceDetachError('ex', 'stack')):  # noqa
            result = send_request()
            tools.eq_(0, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.instances.InstanceBiller.delete_instances', mock_nope)  # noqa
    def test_delete_instances_with_volume_attached(self):
        fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_volume(project_id_1, volume_id='volume_id_a')
        fixtures.insert_instance_volume(
            project_id_1,
            instance_id='instance_id_a',
            volume_id='volume_id_a')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteInstances',
            'instanceIds': ['instance_id_a']
        }))
        tools.eq_(4711, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.instances.InstanceBiller.delete_instances', mock_nope)  # noqa
    def test_delete_instances_with_eip_associated(self):
        fixtures.insert_instance(
            project_id_1,
            instance_id='instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_eip(project_id=project_id_1, eip_id='eip_id_a')
        fixtures.insert_eip_resource(resource_type=eip_model.RESOURCE_TYPE_INSTANCE,  # noqa
                                     resource_id='instance_id_a',
                                     eip_id='eip_id_a')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteInstances',
            'instanceIds': ['instance_id_a']
        }))
        tools.eq_(4712, json.loads(result.data)['retCode'])

    @patches.check_manage()
    def test_manage_describe_instances(self):
        fixtures.insert_instance(instance_id='instance_id_1',
                                 name='instance_name_1',
                                 op_server_id='op_server_id_1')
        fixtures.insert_instance(instance_id='instance_id_2',
                                 name='instance_name_2',
                                 op_server_id='op_server_id_2')

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeInstances'
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])
        tools.eq_(2, len(data['data']['instanceSet']))

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeInstances',
            'instanceIds': ['instance_id_1'],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        instance_set = data['data']['instanceSet']
        tools.eq_(1, len(instance_set))
        tools.eq_('instance_id_1', instance_set[0]['instanceId'])
        tools.eq_('instance_name_1', instance_set[0]['name'])
        tools.eq_('op_server_id_1', instance_set[0]['opServerId'])

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeInstances',
            'instanceIds': ['instance_id_1', 'instance_id_2'],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])
        instance_set = data['data']['instanceSet']
        tools.eq_(2, len(instance_set))

        i = instance_set[0]
        tools.ok_(i['instanceId'] in ('instance_id_1', 'instance_id_2'))
        tools.ok_(i['name'] in ('instance_name_1', 'instance_name_2'))
        tools.ok_(i['opServerId'] in ('op_server_id_1', 'op_server_id_2'))

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeInstances',
            'names': ['instance_name_1', 'instance_name_2'],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])
        tools.eq_(2, len(data['data']['instanceSet']))

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeInstances',
            'opServerIds': ['op_server_id_1', 'op_server_id_2'],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])
        tools.eq_(2, len(data['data']['instanceSet']))
