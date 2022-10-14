import json
import datetime
import env  # noqa
import patches
from nose import tools
from densefog.common import utils
from icebox.model.project import access_key as access_key_model

import fixtures

project_id_1 = 'prjct-1234'


class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_create(self):
        access_key_model.create(project_id_1, 'key1', 'secret')
        access_key1 = access_key_model.get('key1')
        tools.eq_(access_key1['expire_at'],
                  access_key_model.max_expire_time())

        expire_at2 = '2021-12-12T11:11:11Z'
        access_key_model.create(project_id_1, 'key2', 'secret', expire_at2)

        access_key2 = access_key_model.get('key2')
        tools.eq_(access_key2['expire_at'],
                  utils.parse_iso8601(expire_at2))

        d = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        expire_at3 = utils.format_iso8601(d)
        access_key_model.create(project_id_1, 'key3', 'secret', expire_at3)

        access_key3 = access_key_model.get('key3')
        tools.eq_(access_key3['expire_at'],
                  utils.parse_iso8601(expire_at3))

    def test_delete(self):
        fixtures.insert_access_key(project_id_1, 'key1', 'secret')

        access_key1 = access_key_model.get('key1')
        tools.assert_not_equal(access_key1['deleted'], 1)

        access_key_model.delete(project_id_1, ['key1'])

        access_key2 = access_key_model.get('key1')
        tools.eq_(access_key2['deleted'], 1)

    def test_get(self):
        fixtures.insert_access_key(project_id_1, 'key1', 'secret')

        access_key1 = access_key_model.get('key1')

        tools.assert_not_equal(access_key1, None)
        tools.eq_(access_key1['secret'], 'secret')

    def test_limitation(self):
        fixtures.insert_access_key(project_id_1, 'key1', 'secret')
        fixtures.insert_access_key(project_id_1, 'key2', 'secret')
        fixtures.insert_access_key(project_id_1, 'key3', 'secret')

        limit = access_key_model.limitation([project_id_1], reverse=False)
        tools.eq_(limit['total'], 3)
        tools.ok_(limit['items'][0]['key'] in ['key1', 'key2', 'key3'])


@patches.check_manage()
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_send_access_key(self):

        def send_request(key, secret, expire_at=None):
            params = {
                'action': 'CreateAccessKeys',
                'accessKeySet': [{
                    'projectId': project_id_1,
                    'accessKey': key,
                    'accessSecret': secret,
                }]
            }
            if expire_at:
                params['accessKeySet'][0]['expireAt'] = expire_at

            result = fixtures.manage.post('/', data=json.dumps(params))
            return result

        send_request('key1', 'sss')

        access_key1 = access_key_model.get('key1')
        tools.eq_(access_key1['expire_at'],
                  access_key_model.max_expire_time())

        expire_at2 = '2021-12-12T11:11:11Z'
        send_request('key2', 'sss', expire_at2)

        access_key2 = access_key_model.get('key2')
        tools.eq_(access_key2['expire_at'],
                  utils.parse_iso8601(expire_at2))

    def test_delete_access_key(self):
        fixtures.insert_access_key(project_id_1, 'key1', 'secret')
        fixtures.insert_access_key(project_id_1, 'key2', 'secret')

        def send_request(keys):
            result = fixtures.manage.post('/', data=json.dumps({
                'projectId': project_id_1,
                'action': 'DeleteAccessKeys',
                'accessKeySet': keys,
            }))
            return result

        send_request([{
            'projectId': project_id_1,
            'accessKey': 'key1'
        }, {
            'projectId': project_id_1,
            'accessKey': 'key2'
        }])

        tools.eq_(access_key_model.get('key1')['deleted'], 1)
        tools.eq_(access_key_model.get('key2')['deleted'], 1)
