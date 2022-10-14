import json
import env  # noqa
from mock import patch
import patches
from nose import tools
from densefog.common import utils
from densefog.common.utils import MockObject
from icebox.model.project import project as project_model

import fixtures

project_id_1 = 'prjct-1234'

project_id_a = 'project-123-a'
project_id_b = 'project-456-b'


def mock_nope(*args, **kwargs):
    return True


def mock_create_project(*args, **kwargs):
    server = MockObject(**fixtures.op_mock_project)
    server.id = utils.generate_key(32)
    return server


def mock_find_role(*args, **kwargs):
    role = MockObject(**fixtures.op_mock_role)
    return role


def mock_find_user(*args, **kwargs):
    user = MockObject(**fixtures.op_mock_user)
    return user


def mock_op_quota(*args, **kwargs):
    return fixtures.op_mock_update_quota


@patch('novaclient.v2.client.Client.authenticate', mock_nope)
@patch('keystoneclient.v3.projects.ProjectManager.create', mock_create_project)
@patch('keystoneclient.v3.domains.DomainManager.find', mock_nope)
@patch('keystoneclient.v3.projects.ProjectManager.list', mock_nope)
@patch('keystoneclient.v3.projects.ProjectManager.update', mock_nope)
@patch('keystoneclient.v3.projects.ProjectManager.delete', mock_nope)
@patch('keystoneclient.v3.roles.RoleManager.find', mock_find_role)
@patch('keystoneclient.v3.roles.RoleManager.grant', mock_nope)
@patch('keystoneclient.v3.users.UserManager.list', mock_nope)
@patch('keystoneclient.v3.users.UserManager.find', mock_find_user)
@patch('novaclient.v2.quotas.QuotaSetManager.update', mock_nope)
@patch('neutronclient.v2_0.client.Client.update_quota', mock_op_quota)
@patch('cinderclient.v2.quotas.QuotaSetManager.update', mock_nope)
class TestModel:

    def setup(self):
        env.reset_db()

    def test_create(self):
        project_model.create('tnt_id_a', 10, 10, 10, 10, 10, 10, 1000, 10, 10, 10)   # noqa
        project_model.create('tnt_id_b', 10, 10, 10, 10, 10, 10, 1000, 10, 10, 10)   # noqa

        tools.eq_(project_model.limitation()['total'], 2)

    def test_update(self):
        project_id = fixtures.insert_project('project_id_a')
        project_model.update(project_id, **{
            'qt_instances': 1001,
            'qt_vcpus': 1001,
        })

        t = project_model.get(project_id)
        tools.eq_(t['qt_instances'], 1001)
        tools.eq_(t['qt_vcpus'], 1001)

    def test_get(self):
        project_id = fixtures.insert_project('project_id_a')
        t = project_model.get(project_id)
        tools.eq_(t['qt_instances'], 2222)
        tools.eq_(t['qt_vcpus'], 2222)

    def test_limitation(self):
        fixtures.insert_project('project_id_a')
        fixtures.insert_project('project_id_b')

        page = project_model.limitation(reverse=True)

        tools.eq_(page['total'], 2)
        tools.ok_(page['items'][0]['id'] in ['project_id_a', 'project_id_b'])  # noqa


@patch('novaclient.v2.client.Client.authenticate', mock_nope)
@patch('keystoneclient.v3.projects.ProjectManager.create', mock_create_project)
@patch('keystoneclient.v3.projects.ProjectManager.list', mock_nope)
@patch('keystoneclient.v3.projects.ProjectManager.update', mock_nope)
@patch('keystoneclient.v3.projects.ProjectManager.delete', mock_nope)
@patch('keystoneclient.v3.roles.RoleManager.find', mock_find_role)
@patch('keystoneclient.v3.roles.RoleManager.grant', mock_nope)
@patch('keystoneclient.v3.users.UserManager.list', mock_nope)
@patch('keystoneclient.v3.users.UserManager.find', mock_find_user)
@patch('novaclient.v2.quotas.QuotaSetManager.update', mock_nope)
@patch('neutronclient.v2_0.client.Client.update_quota', mock_op_quota)
@patch('cinderclient.v2.quotas.QuotaSetManager.update', mock_nope)
@patches.check_manage()
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_upsert_project(self):

        def send_request(project_id, qt_instances, qt_vcpus):
            result = fixtures.manage.post('/', data=json.dumps({
                'action': 'UpsertProject',
                'projectId': project_id,
                'quotaInstances': qt_instances,
                'quotaVCPUs': qt_vcpus,
                'quotaMemory': 1100,
                'quotaImages': 1100,
                'quotaEIPs': 1100,
                'quotaVolumes': 1100,
                'quotaVolumeSize': 1100,
                'quotaSnapshots': 1100,
                'quotaKeyPairs': 1100,
            }))
            return result

        # insert
        send_request(project_id_1, 1111, 1111)

        project = project_model.get(project_id_1)
        project['qt_instances'] = 1111
        project['qt_vcpus'] = 1111

        # update
        send_request(project_id_1, 2222, 2222)

        project = project_model.get(project_id_1)
        project['qt_instances'] = 2222
        project['qt_vcpus'] = 2222
