import env  # noqa
import json
import patches
from mock import patch
from nose import tools
from densefog.common import utils
from densefog.common.utils import MockObject
from densefog.model.job import job as job_model
from icebox.model.iaas import snapshot as snapshot_model
from icebox.model.iaas import error

import fixtures

project_id_1 = 'prjct-1234'


def mock_snapshot_create(*args, **kwargs):
    snapshot = MockObject(**fixtures.op_mock_snapshot)
    snapshot.id = utils.generate_uuid()
    return snapshot


def mock_nope(*args, **kwargs):
    return True


@patch('cinderclient.v2.client.Client.authenticate', mock_nope)
@patch('cinderclient.v2.volume_snapshots.SnapshotManager.create', mock_snapshot_create)  # noqa
@patch('cinderclient.v2.volume_snapshots.SnapshotManager.delete', mock_nope)
@patch('cinderclient.v2.volume_snapshots.SnapshotManager.update', mock_nope)
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_create(self):
        volume_id = fixtures.insert_volume(project_id=project_id_1)

        snapshot_model.create(
            project_id=project_id_1,
            volume_id=volume_id,
            name='coolname',
            description='cool desc',
            count=2)
        tools.eq_(snapshot_model.limitation()['total'], 2)
        tools.eq_(job_model.limitation()['total'], 1)

    def test_delete(self):
        snapshot_id = fixtures.insert_snapshot(
            project_id=project_id_1,
            snapshot_id='snapshot_id_a',
            status=snapshot_model.SNAPSHOT_STATUS_PENDING)  # noqa

        # should not delete other's snapshots
        fixtures.insert_project('project_id_b')
        with tools.assert_raises(error.ResourceNotBelongsToProject):
            snapshot_model.delete('project_id_b', [snapshot_id])

        # should not delete 'pending' snapshots
        with tools.assert_raises(error.SnapshotCanNotDelete):
            snapshot_model.delete(project_id_1, [snapshot_id])

        snapshot_model.Snapshot.update(snapshot_id, **{
            'status': snapshot_model.SNAPSHOT_STATUS_ACTIVE
        })
        # can delete 'available' snapshots
        snapshot_model.delete(project_id_1, [snapshot_id])
        tools.eq_(snapshot_model.get(snapshot_id)['status'],
                  snapshot_model.SNAPSHOT_STATUS_DELETED)

    def test_modify(self):
        snapshot_id = fixtures.insert_snapshot(project_id_1, 'snapshot_id_a')

        # should not modify other's snapshot
        fixtures.insert_project('project_id_b')
        with tools.assert_raises(error.ResourceNotBelongsToProject):
            snapshot_model.modify('project_id_b', snapshot_id, 'new-snapshot-name')  # noqa

        # modify success
        snapshot_model.modify(project_id_1, snapshot_id, 'new-snapshot-name')

        tools.eq_(snapshot_model.get(snapshot_id)['name'], 'new-snapshot-name')   # noqa

    def test_get(self):
        snapshot_id = fixtures.insert_snapshot(project_id_1, 'snapshot_id_a')

        # not found
        with tools.assert_raises(error.SnapshotNotFound):
            snapshot_model.get('some-other-snapshot')

        tools.eq_(snapshot_model.get(snapshot_id)['project_id'], project_id_1)

    def test_limitation(self):
        fixtures.insert_snapshot(project_id_1, 'snapshot_id_a')
        fixtures.insert_snapshot(project_id_1, 'snapshot_id_b')

        limit = snapshot_model.limitation([project_id_1])
        tools.eq_(limit['total'], 2)
        tools.ok_(limit['items'][0]['id'] in ['snapshot_id_a', 'snapshot_id_b'])   # noqa


@patch('cinderclient.v2.client.Client.authenticate', mock_nope)
@patch('cinderclient.v2.volume_snapshots.SnapshotManager.create', mock_snapshot_create)   # noqa
@patch('cinderclient.v2.volume_snapshots.SnapshotManager.delete', mock_nope)
@patch('cinderclient.v2.volume_snapshots.SnapshotManager.update', mock_nope)
@patches.check_access_key(project_id_1)
class TempTestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_describe_snapshots(self):
        fixtures.insert_snapshot(project_id_1, 'snapshot_id_a')
        fixtures.insert_snapshot(project_id_1, 'snapshot_id_b')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeSnapshots'
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

    def test_describe_snapshots_with_status(self):
        fixtures.insert_snapshot(
            project_id_1, 'snpt-aaa',
            status=snapshot_model.SNAPSHOT_STATUS_ACTIVE)
        fixtures.insert_snapshot(
            project_id_1, 'snpt-bbb',
            status=snapshot_model.SNAPSHOT_STATUS_PENDING)
        fixtures.insert_snapshot(
            project_id_1, 'snpt-ccc',
            status=snapshot_model.SNAPSHOT_STATUS_DELETED)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeSnapshots',
                'status': status
            }))
            return result

        result = send_request([snapshot_model.SNAPSHOT_STATUS_ACTIVE,
                               snapshot_model.SNAPSHOT_STATUS_PENDING])

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    def test_create_snapshots(self):
        volume_id = fixtures.insert_volume(project_id_1, 'volume_id_a')

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'CreateSnapshots',
                'volumeId': volume_id,
                'count': 2
            }))
            return result

        with patch('icebox.model.iaas.openstack.block.create_snapshot',
                   side_effect=Exception('HTTP Connection Error')):
            result = send_request()
            data = json.loads(result.data)
            tools.eq_(data['retCode'], 5001)

        result = send_request()

        data = json.loads(result.data)
        tools.eq_(data['retCode'], 0)
        tools.eq_(len(data['data']['snapshotIds']), 2)
        tools.assert_not_equal(data['data']['jobId'], None)

    def test_delete_snapshots(self):
        fixtures.insert_snapshot(project_id_1, 'snapshot-aaa')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteSnapshots',
            'snapshotIds': ['snapshot-aaa']
        }))
        snapshot_ids = json.loads(result.data)['data']['snapshotIds']
        tools.eq_(len(snapshot_ids), 1)
        tools.eq_(snapshot_ids[0], 'snapshot-aaa')

        snapshot = snapshot_model.get('snapshot-aaa')
        tools.eq_(snapshot['status'], 'deleted')

    def test_modify_snapshot_attributes(self):
        fixtures.insert_snapshot(project_id_1, 'snapshot-aaa')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ModifySnapshotAttributes',
            'snapshotId': 'snapshot-aaa',
            'name': 'new-name',
            'description': 'new-description'
        }))
        snapshot_id = json.loads(result.data)['data']['snapshotId']
        tools.eq_(snapshot_id, 'snapshot-aaa')

        snapshot = snapshot_model.get(snapshot_id)
        tools.eq_(snapshot['name'], 'new-name')
        tools.eq_(snapshot['description'], 'new-description')
