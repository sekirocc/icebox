import env  # noqa
import time
import json
from mock import patch
from nose import tools
import patches
from densefog.common import utils
from densefog.common.utils import MockObject
from densefog.model.journal import operation as operation_model
from icebox.model.iaas import volume as volume_model

import fixtures

project_id_1 = 'prjct-1234'
valid_volume_type = volume_model.SUPPORTED_VOLUME_TYPES[0]


def mock_volume_create(*args, **kwargs):
    mock = MockObject(**fixtures.op_mock_volume)
    mock.id = utils.generate_uuid()
    return mock


def mock_nope(*args, **kwargs):
    return True


@patch('cinderclient.v2.client.Client.authenticate', mock_nope)
@patches.nova_authenticate
class Test:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('cinderclient.v2.volumes.VolumeManager.create', mock_volume_create)
    @patch('icebox.model.iaas.volume.Volume.status_deletable', mock_nope)  # noqa
    @patches.check_access_key(project_id_1)
    def test_create(self):
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'CreateVolumes',
            'size': 1, 'count': 1,
            'volumeType': valid_volume_type,
        }))
        volume_ids = json.loads(result.data)['data']['volumeIds']

        time.sleep(1)
        fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteVolumes',
            'volumeIds': volume_ids
        }))

        time.sleep(1)
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'CreateVolumes',
            'size': 1, 'count': 3,
            'volumeType': valid_volume_type,
        }))
        volume_ids = json.loads(result.data)['data']['volumeIds']

        time.sleep(1)
        fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteVolumes',
            'volumeIds': volume_ids
        }))

        time.sleep(1)
        fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteVolumes',
            'volumeIds': ['some-other-volume-id']
        }))

        limit = operation_model.limitation(
            project_ids=[project_id_1], reverse=False)
        tools.eq_(limit['total'], 5)

        op2 = limit['items'][2]
        tools.eq_(op2['ret_code'], 0)
        tools.eq_(op2['ret_message'], 'good job.')
        tools.eq_(op2['action'], 'CreateVolumes')
        params = json.loads(op2['params'])
        tools.eq_(params['size'], 1)
        tools.eq_(params['count'], 3)
        tools.eq_(op2['resource_type'], 'volume')
        volume_ids = json.loads(op2['resource_ids'])
        tools.eq_(3, len(volume_ids))

        op4 = limit['items'][4]
        tools.eq_(op4['ret_code'], 4104)
        tools.eq_(op4['ret_message'], 'Volume (some-other-volume-id) is not found')  # noqa
        tools.eq_(op4['action'], 'DeleteVolumes')
        params = json.loads(op4['params'])
        tools.eq_(params['volumeIds'][0], 'some-other-volume-id')
        tools.eq_(op4['resource_type'], 'volume')
        volume_ids = json.loads(op4['resource_ids'])
        tools.eq_(1, len(volume_ids))

        for i, v in enumerate(['CreateVolumes',
                               'DeleteVolumes',
                               'CreateVolumes',
                               'DeleteVolumes',
                               'DeleteVolumes']):
            tools.eq_(limit['items'][i]['action'], v)

    @patches.check_access_key(project_id_1)
    def test_describe_operations(self):
        fixtures.insert_operation(project_id=project_id_1, action='CreateVolumes')   # noqa
        fixtures.insert_operation(project_id=project_id_1, action='DeleteVolumes')   # noqa
        fixtures.insert_operation(project_id=project_id_1, action='CreateVolumes')   # noqa
        fixtures.insert_operation(project_id=project_id_1, action='DeleteVolumes')   # noqa
        fixtures.insert_operation(project_id=project_id_1, action='DeleteVolumes')   # noqa

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeOperations',
        }))

        data = json.loads(result.data)
        tools.eq_(data['retCode'], 0)
        tools.eq_(len(data['data']['operationSet']), 5)
