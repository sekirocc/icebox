import env  # noqa
import json
import patches
from mock import patch
from nose import tools
from densefog.common import utils
from densefog.common.utils import MockObject
from densefog.model.job import job as job_model
from icebox.model.iaas import volume as volume_model
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import instance_volume as instance_volume_model
from icebox.model.iaas import error as iaas_error

import fixtures

project_id_1 = 'prjct-1234'
valid_volume_type = volume_model.SUPPORTED_VOLUME_TYPES[0]


def mock_volume_create(*args, **kwargs):
    volume = MockObject(**fixtures.op_mock_volume)
    volume.id = utils.generate_uuid()
    return volume


def mock_volume_get(*args, **kwargs):
    volume = MockObject(**fixtures.op_mock_volume)
    volume.id = utils.generate_uuid()
    return volume


def mock_nope(*args, **kwargs):
    return True


@patch('icebox.model.iaas.openstack.api.do_create_data_volume', mock_volume_create)  # noqa
@patch('icebox.model.iaas.openstack.api.do_attach_volume', mock_nope)
@patch('icebox.model.iaas.openstack.api.do_detach_volume', mock_nope)
@patch('icebox.model.iaas.openstack.api.do_extend_volume', mock_nope)
@patch('icebox.model.iaas.openstack.api.do_get_volume', mock_volume_get)
@patch('icebox.model.iaas.openstack.api.do_delete_volume', mock_nope)
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_create(self):
        with tools.assert_raises(iaas_error.VolumeCreateParamError):
            volume_model.create(project_id=project_id_1, count=1,
                                size=1)

        with tools.assert_raises(iaas_error.VolumeCreateParamError):
            volume_model.create(project_id=project_id_1, count=1,
                                volume_type=valid_volume_type)

        with tools.assert_raises(iaas_error.VolumeCreateVolumeTypeNotSupportError):  # noqa
            volume_model.create(project_id=project_id_1, count=1,
                                size=1,
                                volume_type='some-unsupported-type')

        # can create by volume_type & size
        volume_model.create(project_id=project_id_1, count=1,
                            size=1,
                            volume_type=valid_volume_type)

        snapshot_id = fixtures.insert_snapshot(project_id=project_id_1)
        # can create by snapshot
        volume_model.create(project_id=project_id_1, count=1,
                            snapshot_id=snapshot_id)

        tools.eq_(volume_model.limitation()['total'], 2)
        tools.eq_(job_model.limitation()['total'], 2)

    def test_delete(self):
        volume_id = fixtures.insert_volume(
            project_id=project_id_1,
            volume_id='volume_id_a',
            status=volume_model.VOLUME_STATUS_PENDING)

        # should not delete other's volumes
        project_id = fixtures.insert_project('some-project')
        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            volume_model.delete(project_id, [volume_id])

        # should not delete 'pending' volumes
        with tools.assert_raises(iaas_error.VolumeCanNotDelete):
            volume_model.delete(project_id_1, [volume_id])

        volume_model.Volume.update(volume_id, **{
            'status': volume_model.VOLUME_STATUS_ACTIVE
        })
        # can delete 'available' volumes
        volume_model.delete(project_id_1, [volume_id])
        tools.eq_(volume_model.get(volume_id)['status'],
                  volume_model.VOLUME_STATUS_DELETED)

    def test_attach(self):
        instance_id = fixtures.insert_instance(project_id_1, 'inst-id-1')
        volume_id = fixtures.insert_volume(project_id_1, 'volume-id-1')

        def reset_status():
            instance_model.Instance.update(instance_id, **{
                'status': instance_model.INSTANCE_STATUS_ACTIVE
            })
            volume_model.Volume.update(volume_id, **{
                'status': volume_model.VOLUME_STATUS_ACTIVE
            })

        # should not attach other's volumes
        fixtures.insert_project('project_id_b')
        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            volume_model.attach('project_id_b',
                                volume_id,
                                instance_id)

        reset_status()
        instance_model.Instance.update(instance_id, **{
            'status': instance_model.INSTANCE_STATUS_PENDING
        })
        # instance should be status_attachable
        with tools.assert_raises(iaas_error.InstanceCanNotBeAttached):
            volume_model.attach(project_id_1, volume_id, instance_id)  # noqa

        reset_status()
        volume_model.Volume.update(volume_id, **{
            'status': volume_model.VOLUME_STATUS_PENDING
        })
        # volume should be status_attachable
        with tools.assert_raises(iaas_error.VolumeCanNotAttach):
            volume_model.attach(project_id_1, volume_id, instance_id)  # noqa

        reset_status()

        volume_model.attach(project_id_1, volume_id, instance_id)

        tools.eq_(volume_model.get(volume_id)['status'], volume_model.VOLUME_STATUS_ATTACHING)  # noqa
        instance_volume = instance_volume_model.get(volume_id=volume_id)
        tools.eq_(instance_volume['instance_id'], instance_id)

        tools.eq_(job_model.limitation()['total'], 1)

    def test_detach(self):
        fixtures.insert_volume(project_id_1, 'volume_id_a',
                               status=volume_model.VOLUME_STATUS_IN_USE)
        fixtures.insert_instance(project_id_1, 'instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_instance_volume(project_id_1,
                                        'volume_id_a', 'instance_id_a')
        # should not detach other's volume
        fixtures.insert_project('project_id_b')
        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            volume_model.detach('project_id_b', ['volume_id_a'], 'instance_id_a')  # noqa

        fixtures.insert_volume(project_id_1, 'volume_id_b',
                               status=volume_model.VOLUME_STATUS_IN_USE)
        fixtures.insert_instance(project_id_1, 'instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)  # noqa
        fixtures.insert_instance_volume(project_id_1, 'volume_id_b', 'instance_id_b')  # noqa

        # detach success
        volume_model.detach(project_id_1, ['volume_id_b'], 'instance_id_b')
        tools.eq_(volume_model.get('volume_id_b')['status'],
                  volume_model.VOLUME_STATUS_DETACHING)

        with tools.assert_raises(iaas_error.InstanceVolumeNotFound):
            instance_volume_model.get(volume_id='volume_id_b')

    def test_detach_with_status(self):
        fixtures.insert_volume(project_id_1, 'volume_id_a',
                               status=volume_model.VOLUME_STATUS_IN_USE)
        fixtures.insert_instance(project_id_1, 'instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_STARTING)  # noqa
        fixtures.insert_instance_volume(project_id_1,
                                        'volume_id_a', 'instance_id_a')
        # should not detach a volume from busy instance
        with tools.assert_raises(iaas_error.InstanceCanNotBeDetached):
            volume_model.detach(project_id_1, ['volume_id_a'], 'instance_id_a')

        fixtures.insert_volume(project_id_1, 'volume_id_b',
                               status=volume_model.VOLUME_STATUS_BACKING_UP)
        fixtures.insert_instance(project_id_1, 'instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_instance_volume(project_id_1,
                                        'volume_id_b', 'instance_id_b')
        # should not detach a backing up volume
        with tools.assert_raises(iaas_error.VolumeCanNotDetach):
            volume_model.detach(project_id_1, ['volume_id_b'], 'instance_id_b')

    def test_detach_with_not_attach(self):
        fixtures.insert_volume(project_id_1, 'volume_id_a',
                               status=volume_model.VOLUME_STATUS_IN_USE)
        fixtures.insert_instance(project_id_1, 'instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_instance(project_id_1, 'instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)

        fixtures.insert_instance_volume(project_id_1,
                                        'volume_id_a', 'instance_id_a')
        # should not detach a volume that is not attached the instance
        with tools.assert_raises(iaas_error.DetachVolumeWhenNotAttached):
            volume_model.detach(project_id_1, ['volume_id_a'], 'instance_id_b')

    def test_extend(self):
        volume_id = fixtures.insert_volume(project_id_1, 'volume_id_a')

        def reset_status():
            volume_model.Volume.update(volume_id, **{
                'status': volume_model.VOLUME_STATUS_ACTIVE
            })

        # should not extend other's volume
        project_id = fixtures.insert_project('project_id_b')
        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            volume_model.extend(project_id, [volume_id], 2)

        reset_status()
        volume_model.Volume.update(volume_id, **{
            'status': volume_model.VOLUME_STATUS_ATTACHING
        })
        # should not extend busy volume
        with tools.assert_raises(iaas_error.VolumeCanNotExtend):
            volume_model.extend(project_id_1, [volume_id], 2)

        reset_status()
        # should not extend to a equal or less size
        with tools.assert_raises(iaas_error.VolumeNewSizeTooSmall):
            volume_model.extend(project_id_1, [volume_id], 1)

        # extend success
        volume_model.extend(project_id_1, [volume_id], 2)
        tools.eq_(volume_model.get(volume_id)['status'], volume_model.VOLUME_STATUS_PENDING)  # noqa
        tools.eq_(job_model.limitation()['total'], 1)

    def test_modify(self):
        volume_id = fixtures.insert_volume(project_id_1, 'volume_id_a')

        # should not modify other's volume
        fixtures.insert_project('project_id_b')
        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            volume_model.modify('project_id_b', volume_id, 'new-vol-name')  # noqa

        # modify success
        volume_model.modify(project_id_1, volume_id, 'new-vol-name')

        tools.eq_(volume_model.get(volume_id)['name'], 'new-vol-name')

    def test_get(self):
        volume_id = fixtures.insert_volume(project_id_1, 'volume_id_a')

        # not found
        with tools.assert_raises(iaas_error.VolumeNotFound):
            volume_model.get('some-other-volume')

        tools.eq_(volume_model.get(volume_id)['project_id'], project_id_1)

    def test_limitation(self):
        fixtures.insert_volume(project_id_1, 'volume_id_a')
        fixtures.insert_volume(project_id_1, 'volume_id_b')

        limit = volume_model.limitation([project_id_1])
        tools.eq_(limit['total'], 2)
        tools.ok_(limit['items'][0]['id'] in ['volume_id_a', 'volume_id_b'])

    def test_sync(self):
        pass

    def test_partially_success_action(self):
        # partially success create action
        with patch('icebox.model.iaas.openstack.api.do_create_data_volume',  # noqa
                   side_effect=iaas_error.ProviderCreateVolumeError('ex', 'stack')):  # noqa
            with tools.assert_raises(iaas_error.ActionsPartialSuccessError) as cm:  # noqa
                volume_model.create(
                    project_id=project_id_1,
                    size=1,
                    name='coolname',
                    volume_type=valid_volume_type,
                    count=2)

            exc = cm.exception
            tools.eq_(exc.job_id, None)
            tools.eq_(len(exc.exceptions), 2)
            tools.ok_(isinstance(exc.exceptions[0]['exception'],
                                 iaas_error.ProviderCreateVolumeError))
            tools.ok_(isinstance(exc.exceptions[1]['exception'],
                                 iaas_error.ProviderCreateVolumeError))


# @patch('cinderclient.v2.client.Client.authenticate', mock_nope)
# @patch('cinderclient.v2.volumes.VolumeManager.create', mock_volume_create)
# @patch('cinderclient.v2.volumes.VolumeManager.delete', mock_nope)
# @patch('novaclient.v2.volumes.VolumeManager.create_server_volume', mock_nope)
# @patch('novaclient.v2.volumes.VolumeManager.delete_server_volume', mock_nope)
# @patch('cinderclient.v2.volumes.VolumeManager.extend', mock_nope)
# @patch('cinderclient.v2.volumes.VolumeManager.update', mock_nope)

@patch('icebox.model.iaas.openstack.api.do_create_data_volume', mock_volume_create)  # noqa
@patch('icebox.model.iaas.openstack.api.do_attach_volume', mock_nope)
@patch('icebox.model.iaas.openstack.api.do_detach_volume', mock_nope)
@patch('icebox.model.iaas.openstack.api.do_extend_volume', mock_nope)
@patch('icebox.model.iaas.openstack.api.do_get_volume', mock_volume_get)
@patch('icebox.model.iaas.openstack.api.do_delete_volume', mock_nope)
@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_describe_volumes(self):
        volume_id = fixtures.insert_volume(project_id_1, 'volume_id_a')
        instance_id = fixtures.insert_instance(
            project_id_1, 'inst-id-1',
            status=instance_model.INSTANCE_STATUS_ACTIVE)

        volume_model.attach(project_id_1, volume_id, instance_id)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeVolumes'
        }))
        data = json.loads(result.data)

        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        tools.eq_(1, len(data['data']['volumeSet']))

        tools.eq_(instance_id, data['data']['volumeSet'][0]['instanceId'])

        with tools.assert_raises(KeyError):
            tools.ok_(data['data']['volumeSet'][0]['instance'])

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeVolumes',
            'verbose': True
        }))
        data = json.loads(result.data)

        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        tools.eq_(1, len(data['data']['volumeSet']))

        tools.eq_(instance_id, data['data']['volumeSet'][0]['instanceId'])
        tools.eq_(instance_id, data['data']['volumeSet'][0]['instance']['instanceId'])  # noqa

    def test_describe_volumes_with_status(self):
        fixtures.insert_volume(
            project_id=project_id_1, volume_id='volm-aaa',
            status=volume_model.VOLUME_STATUS_ACTIVE)
        fixtures.insert_volume(
            project_id=project_id_1, volume_id='volm-bbb',
            status=volume_model.VOLUME_STATUS_PENDING)
        fixtures.insert_volume(
            project_id=project_id_1, volume_id='volm-ccc',
            status=volume_model.VOLUME_STATUS_DELETED)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeVolumes',
                'status': status
            }))
            return result

        result = send_request([volume_model.VOLUME_STATUS_ACTIVE,
                               volume_model.VOLUME_STATUS_PENDING])

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    def test_create_volumes(self):

        def send_request(size=None, volume_type=None, snapshot_id=None):
            params = {'action': 'CreateVolumes', 'count': 2}
            if snapshot_id:
                params['snapshotId'] = snapshot_id
            if volume_type:
                params['volumeType'] = volume_type
            if size:
                params['size'] = size
            result = fixtures.public.post('/', data=json.dumps(params))
            return result

        with patch('icebox.model.iaas.openstack.api.do_create_data_volume',  # noqa
                   side_effect=iaas_error.ProviderCreateVolumeError('ex', 'stack')):  # noqa
            result = send_request(size=1, volume_type=valid_volume_type)
            data = json.loads(result.data)
            tools.eq_(data['retCode'], 5001)

        result = send_request(size=1)
        data = json.loads(result.data)
        tools.eq_(data['retCode'], 4100)

        result = send_request(volume_type=valid_volume_type)
        data = json.loads(result.data)
        tools.eq_(data['retCode'], 4100)

        result = send_request(size=1, volume_type='unsupported-type')
        data = json.loads(result.data)
        tools.eq_(data['retCode'], 4100)

        result = send_request(size=1, volume_type=valid_volume_type)
        data = json.loads(result.data)
        tools.eq_(data['retCode'], 0)
        tools.eq_(len(data['data']['volumeIds']), 2)
        tools.assert_not_equal(data['data']['jobId'], None)

        snapshot_id = fixtures.insert_snapshot(project_id=project_id_1)
        result = send_request(snapshot_id=snapshot_id)
        data = json.loads(result.data)
        tools.eq_(data['retCode'], 0)
        tools.eq_(len(data['data']['volumeIds']), 2)
        tools.assert_not_equal(data['data']['jobId'], None)

    def test_delete_volumes(self):
        fixtures.insert_volume(project_id_1, 'volume-aaa')
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteVolumes',
            'volumeIds': ['volume-aaa']
        }))
        volume_ids = json.loads(result.data)['data']['volumeIds']
        tools.eq_(len(volume_ids), 1)
        tools.eq_(volume_ids[0], 'volume-aaa')

        volume = volume_model.get('volume-aaa')
        tools.eq_(volume['status'], 'deleted')

    def test_attach_volume(self):
        volume_id = fixtures.insert_volume(project_id_1, 'volume_id_a')
        instance_id = fixtures.insert_instance(
            project_id_1, 'instance_id_a',
            status=instance_model.INSTANCE_STATUS_ACTIVE)  # noqa

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'AttachVolume',
                'instanceId': instance_id,
                'volumeId': volume_id,
            }))
            return result

        with patch('icebox.model.iaas.openstack.api.do_attach_volume',
                   side_effect=iaas_error.ProviderCreateServerVolumeError('ex', 'stack')):  # noqa
            result = send_request()
            tools.eq_(json.loads(result.data)['retCode'], 5001)

        result = send_request()

        data = json.loads(result.data)
        tools.assert_not_equal(data['data']['jobId'], None)
        tools.eq_(data['data']['volumeId'], volume_id)

        volume = volume_model.get(volume_id)
        instance_volume = instance_volume_model.get(volume_id, instance_id)  # noqa
        tools.eq_(volume['status'], volume_model.VOLUME_STATUS_ATTACHING)

    def test_detach_volumes(self):
        fixtures.insert_volume(project_id_1, 'volume_id_a',
                               status=volume_model.VOLUME_STATUS_IN_USE)
        fixtures.insert_instance(project_id_1, 'instance_id_a',
                                 status=volume_model.VOLUME_STATUS_ACTIVE)

        fixtures.insert_instance_volume(project_id_1,
                                        'volume_id_a', 'instance_id_a')

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DetachVolumes',
                'instanceId': 'instance_id_a',
                'volumeIds': ['volume_id_a']
            }))
            return result

        with patch('icebox.model.iaas.openstack.api.do_detach_volume',
                   side_effect=iaas_error.ProviderDeleteServerVolumeError('ex', 'stack')):  # noqa
            result = send_request()
            tools.eq_(json.loads(result.data)['retCode'], 5001)

        result = send_request()

        data = json.loads(result.data)
        tools.assert_not_equal(data['data']['jobId'], None)
        tools.eq_(data['data']['volumeIds'][0], 'volume_id_a')

        with tools.assert_raises(iaas_error.InstanceVolumeNotFound):
            instance_volume_model.get('volume_id_a', 'instance_id_a')

        volume = volume_model.get('volume_id_a')
        tools.eq_(volume['status'], volume_model.VOLUME_STATUS_DETACHING)

    def test_detach_volumes_with_not_attach(self):
        fixtures.insert_volume(project_id_1, 'volume_id_a',
                               status=volume_model.VOLUME_STATUS_IN_USE)
        fixtures.insert_instance(project_id_1, 'instance_id_a',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)
        fixtures.insert_instance(project_id_1, 'instance_id_b',
                                 status=instance_model.INSTANCE_STATUS_ACTIVE)

        fixtures.insert_instance_volume(project_id_1,
                                        'volume_id_a', 'instance_id_a')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DetachVolumes',
            'instanceId': 'instance_id_b',
            'volumeIds': ['volume_id_a']
        }))
        tools.eq_(4721, json.loads(result.data)['retCode'])

    def test_extend_volumes(self):
        fixtures.insert_volume(project_id_1, 'volume-aaa')

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'ExtendVolumes',
                'size': 2,
                'volumeIds': ['volume-aaa']
            }))
            return result

        with patch('icebox.model.iaas.openstack.api.do_extend_volume',
                   side_effect=iaas_error.ProviderExtendVolumeError('ex', 'stack')):  # noqa
            result = send_request()
            tools.eq_(json.loads(result.data)['retCode'], 5001)

        result = send_request()
        volume_ids = json.loads(result.data)['data']['volumeIds']
        tools.eq_(len(volume_ids), 1)
        tools.eq_(volume_ids[0], 'volume-aaa')

        volume = volume_model.get('volume-aaa')
        tools.eq_(volume['size'], 2)

    def test_modify_volume_attributes(self):
        fixtures.insert_volume(project_id_1, 'volume-aaa')
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ModifyVolumeAttributes',
            'volumeId': 'volume-aaa',
            'name': 'new-name',
            'description': 'new-description'
        }))
        volume_id = json.loads(result.data)['data']['volumeId']
        tools.eq_(volume_id, 'volume-aaa')

        volume = volume_model.get('volume-aaa')
        tools.eq_(volume['name'], 'new-name')
        tools.eq_(volume['description'], 'new-description')
