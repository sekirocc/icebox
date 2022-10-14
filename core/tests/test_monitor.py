import env  # noqa
import patches
import fixtures
import json
from mock import patch
from nose import tools
from densefog.common import utils


project_id_1 = 'prjct-1234'


def mock_list(*args, **kwargs):
    return fixtures.op_mock_get_monitor


def mock_nope(*args, **kwargs):
    return None


@patches.nova_authenticate
@patch('ceilometerclient.v2.statistics.StatisticsManager.list', mock_list)
@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('keystoneclient.adapter.Adapter.get', mock_nope)
    def test_get_monitor(self):
        rand_id = utils.generate_key(32)
        fixtures.insert_instance_type(project_id=project_id_1, instance_type_id=rand_id)  # noqa
        fixtures.insert_image(project_id=project_id_1, image_id=rand_id)
        fixtures.insert_network(project_id=project_id_1, network_id=rand_id)
        fixtures.insert_subnet(project_id=project_id_1, subnet_id=rand_id)
        instance_id = fixtures.insert_instance(project_id_1)

        metrics = [
            'instance.cpu',
            'instance.memory',
            'instance.disk.usage',
            'instance.disk.iops',
            'instance.disk.io',
            'instance.network.traffic',
            'instance.network.packets',
            'volume.usage',
            'volume.iops',
            'volume.io',
            'eip.traffic',
            'eip.packets',
        ]

        for period in [
            '120mins',
            '720mins',
            '48hours',
            '14days',
            '30days',
        ]:
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'GetMonitor',
                'resourceIds': [instance_id],
                'metrics': metrics,
                'period': period,
            }))
            tools.eq_(200, result.status_code)
            tools.eq_(0, json.loads(result.data)['retCode'])
            tools.eq_(
                len(metrics),
                len(json.loads(result.data)['data']['monitorSet']))
            tools.eq_(
                instance_id,
                json.loads(result.data)['data']['monitorSet'][0]['resourceId'])
