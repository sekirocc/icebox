import env  # noqa
import patches
import json
from mock import patch
from nose import tools
from icebox.model.iaas import key_pair as key_pair_model

import fixtures
import fixtures_openstack as op_fixtures

project_id_1 = 'prjct-1234'


def mock_create_key_pair(*args, **kwargs):
    return op_fixtures.op_mock_key_pair


@patches.nova_authenticate
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('icebox.model.iaas.openstack.api.do_create_keypair', mock_create_key_pair)  # noqa
    def test_create(self):
        key_pair_id, public_key = key_pair_model.create(
            project_id=project_id_1,
            name='name_a')
        tools.eq_(key_pair_model.limitation()['total'], 1)

    def test_delete(self):
        key_pair_id = fixtures.insert_key_pair(project_id=project_id_1)

        key_pair_model.delete(project_id_1, [key_pair_id])
        tools.eq_(key_pair_model.limitation()['total'], 1)
        tools.eq_(key_pair_model.get(key_pair_id)['status'], 'deleted')

    def test_limitation(self):
        key_pair_id = fixtures.insert_key_pair(project_id=project_id_1)

        tools.eq_(key_pair_model.limitation(
            project_ids=[project_id_1])['total'], 1)
        tools.eq_(key_pair_model.limitation(
            project_ids=[])['total'], 0)

        tools.eq_(key_pair_model.limitation(
            status=[key_pair_model.KEY_PAIR_STATUS_ACTIVE])['total'], 1)
        tools.eq_(key_pair_model.limitation(
            status=[key_pair_model.KEY_PAIR_STATUS_DELETED])['total'], 0)

        tools.eq_(key_pair_model.limitation(
            key_pair_ids=[key_pair_id])['total'], 1)
        tools.eq_(key_pair_model.limitation(
            key_pair_ids=[])['total'], 0)

        tools.eq_(key_pair_model.limitation(
            search_word=key_pair_id)['total'], 1)


@patches.nova_authenticate
@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_public_describe_key_pairs(self):
        fixtures.insert_key_pair(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeKeyPairs'
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(1, json.loads(result.data)['data']['total'])

    def test_public_describe_key_pairs_with_status(self):
        fixtures.insert_key_pair(
            project_id=project_id_1, key_pair_id='kp-aaa',
            status=key_pair_model.KEY_PAIR_STATUS_ACTIVE)
        fixtures.insert_key_pair(
            project_id=project_id_1, key_pair_id='kp-bbb',
            status=key_pair_model.KEY_PAIR_STATUS_ACTIVE)
        fixtures.insert_key_pair(
            project_id=project_id_1, key_pair_id='kp-ccc',
            status=key_pair_model.KEY_PAIR_STATUS_DELETED)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeKeyPairs',
                'status': status
            }))
            return result

        result = send_request([key_pair_model.KEY_PAIR_STATUS_ACTIVE])

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    @patch('icebox.model.iaas.openstack.api.do_create_keypair', mock_create_key_pair)  # noqa
    def test_public_create_key_pair(self):
        result = fixtures.public.post('/', data=json.dumps({
            'action': 'CreateKeyPair',
            'name': 'name_a',
        }))
        key_pair_id = json.loads(result.data)['data']['keyPairId']

        tools.eq_(key_pair_model.limitation(
            key_pair_ids=[key_pair_id])['total'], 1)

    def test_public_delete_key_pair(self):
        key_pair_id = fixtures.insert_key_pair(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeleteKeyPairs',
            'keyPairIds': [key_pair_id],
        }))
        key_pair_ids = json.loads(result.data)['data']['keyPairIds']
        tools.eq_(len(key_pair_ids), 1)
        tools.eq_(key_pair_ids[0], key_pair_id)

        tools.eq_(key_pair_model.limitation(
            status=[key_pair_model.KEY_PAIR_STATUS_DELETED])['total'], 1)

    def test_modify_key_pair_attributes(self):
        key_pair_id = fixtures.insert_key_pair(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ModifyKeyPairAttributes',
            'keyPairId': key_pair_id,
            'name': 'kp_123',
            'description': 'desc_123',
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        key_pair = key_pair_model.limitation(key_pair_ids=[key_pair_id])['items'][0]  # noqa
        tools.eq_(key_pair['name'], 'kp_123')
        tools.eq_(key_pair['description'], 'desc_123')
