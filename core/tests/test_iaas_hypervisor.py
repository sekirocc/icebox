import env  # noqa
import patches
import json
from mock import patch
from nose import tools
from densefog.common import utils
from densefog.common.utils import MockObject
from icebox.model.iaas import hypervisor as hypervisor_model
import fixtures


def mock_list_hypervisors():
    mock1 = MockObject(**fixtures.op_hypervisor_example)
    mock1.id = utils.generate_key(36)
    mock2 = MockObject(**fixtures.op_hypervisor_example)
    mock2.id = utils.generate_key(36)

    return [mock1, mock2]


@patches.nova_authenticate
class TestModel:

    @staticmethod
    def setup():
        env.reset_db()

    def test_get(self):
        hyper_id_a = fixtures.insert_hypervisor(
            hypervisor_id='hyper_id_a',
            status=hypervisor_model.HYPERVISOR_STATUS_ENABLED)

        hypervisor = hypervisor_model.get(hyper_id_a)
        tools.eq_(hypervisor['status'],
                  hypervisor_model.HYPERVISOR_STATUS_ENABLED)

    def test_limitation(self):
        fixtures.insert_hypervisor(hypervisor_id='hyper_id_a')
        fixtures.insert_hypervisor(hypervisor_id='hyper_id_b')
        fixtures.insert_hypervisor(
            hypervisor_id='hyper_id_c',
            status=hypervisor_model.HYPERVISOR_STATUS_DISABLED)

        tools.eq_(hypervisor_model.limitation()['total'], 3)
        tools.eq_(hypervisor_model.limitation(
            status=[hypervisor_model.HYPERVISOR_STATUS_DISABLED])['total'], 1)

    def test_modify(self):
        hyper_id_a = fixtures.insert_hypervisor(hypervisor_id='hyper_id_a')
        hyper_description_a = 'blabla'
        hypervisor_model.modify(hyper_id_a, description=hyper_description_a)
        tools.eq_(hypervisor_model.get(hyper_id_a)['description'],
                  hyper_description_a)

    @patch('icebox.model.iaas.openstack.api.do_list_hypervisors', mock_list_hypervisors)  # noqa
    def test_sync_all(self, ):
        hypervisor_model.sync_all()


@patches.nova_authenticate
@patches.check_manage()
class TestAPI:

    @staticmethod
    def setup():
        env.reset_db()

    def test_manage_describe_hypervisors(self):
        fixtures.insert_hypervisor(hypervisor_id='hyper_id_a')
        fixtures.insert_hypervisor(
            hypervisor_id='hyper_id_b',
            status=hypervisor_model.HYPERVISOR_STATUS_DISABLED)

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeHypervisors',
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeHypervisors',
            'status': [hypervisor_model.HYPERVISOR_STATUS_DISABLED]
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        tools.eq_(data['data']['hypervisorSet'][0]['status'],
                  hypervisor_model.HYPERVISOR_STATUS_DISABLED)

    def test_manage_modify_hypervisor(self):
        hyper_id_a = fixtures.insert_hypervisor()
        hyper_description_a = 'blabla'

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'ModifyHypervisorAttributes',
            'hypervisorId': hyper_id_a,
            'description': hyper_description_a,
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(hypervisor_model.get(hyper_id_a)['description'],
                  hyper_description_a)
