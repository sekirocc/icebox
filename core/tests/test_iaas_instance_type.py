import env  # noqa
import patches
import json
from mock import patch
from nose import tools
from densefog.common import utils
from icebox.model.iaas import instance_type as instance_type_model

import fixtures

project_id_1 = 'prjct-123'


def mock_create(*argvs, **kwargs):
    mock = utils.MockObject(**fixtures.op_mock_flavor)
    mock.id = utils.generate_uuid()
    return mock


def mock_none(*argvs, **kwargs):
    return None


@patches.nova_authenticate
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('icebox.model.iaas.openstack.api.do_find_flavor', mock_none)
    @patch('icebox.model.iaas.openstack.api.do_create_flavor', mock_create)
    @patch('icebox.model.iaas.openstack.api.do_update_flavor_quota', mock_none)  # noqa
    def test_generate(self):
        instance_type_model.generate()
        instance_type_model.generate()

    def test_limitation(self):
        fixtures.insert_instance_type(
            instance_type_id='inst_type_a',
            project_id=instance_type_model.PUBLIC_INSTANCE_TYPE)

        tools.eq_(instance_type_model.limitation()['total'], 1)


@patches.nova_authenticate
@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_public_describe_key_pairs(self):
        fixtures.insert_instance_type(
            instance_type_id='inst_type_a',
            project_id=instance_type_model.PUBLIC_INSTANCE_TYPE)
        fixtures.insert_instance_type(
            instance_type_id='inst_type_b',
            project_id=instance_type_model.PUBLIC_INSTANCE_TYPE)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeInstanceTypes',
            'isPublic': True,
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeInstanceTypes',
            'isPublic': False,
        }))
        tools.eq_(0, json.loads(result.data)['data']['total'])

    def test_public_describe_key_pairs_with_status(self):
        fixtures.insert_instance_type(
            project_id=instance_type_model.PUBLIC_INSTANCE_TYPE,
            instance_type_id='inst_type_a',
            status=instance_type_model.INSTANCE_TYPE_STATUS_ACTIVE)
        fixtures.insert_instance_type(
            project_id=instance_type_model.PUBLIC_INSTANCE_TYPE,
            instance_type_id='inst_type_b',
            status=instance_type_model.INSTANCE_TYPE_STATUS_ACTIVE)
        fixtures.insert_instance_type(
            project_id=instance_type_model.PUBLIC_INSTANCE_TYPE,
            instance_type_id='inst_type_c',
            status=instance_type_model.INSTANCE_TYPE_STATUS_DELETED)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeInstanceTypes',
                'status': status
            }))
            return result

        result = send_request([instance_type_model.INSTANCE_TYPE_STATUS_ACTIVE])  # noqa

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])
