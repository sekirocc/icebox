# import json
import time
# import gevent
# from gevent import monkey
import threading
from copy import copy
import env  # noqa
from mock import patch
from nose import tools
from densefog.common import utils
from densefog.common.utils import MockObject
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas.openstack import compute as compute_provider
from icebox.model.project import project as project_model
from densefog.model import base

import fixtures

project_id_1 = 'prjct-1234'


def mock_get_server(*args, **kwargs):
    server = copy(fixtures.op_mock_server)
    server['OS-EXT-STS:task_state'] = None
    server['OS-EXT-STS:power_state'] = compute_provider.SERVER_POWER_STATE_SHUTDOWN  # noqa
    server['id'] = utils.generate_uuid()

    server = MockObject(**server)
    return server


def mock_stop_server(*args, **kwargs):
    time.sleep(5)


def mock_nope(*args, **kwargs):
    return True


def create_instance(instance_id, status=instance_model.INSTANCE_STATUS_ACTIVE):  # noqa
    rand_id = utils.generate_key(32)
    fixtures.insert_instance_type(project_id=project_id_1, instance_type_id=rand_id)  # noqa
    fixtures.insert_image(project_id=project_id_1, image_id=rand_id)
    fixtures.insert_network(project_id=project_id_1, network_id=rand_id)
    fixtures.insert_subnet(project_id=project_id_1, network_id=rand_id, subnet_id=rand_id)  # noqa
    fixtures.insert_instance(project_id=project_id_1, instance_id=instance_id, network_id=rand_id, subnet_id=rand_id, status=status)  # noqa

    return instance_id


@patch('neutronclient.v2_0.client.Client.delete_port', mock_nope)
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('novaclient.v2.client.Client.authenticate', mock_nope)
    @patch('novaclient.v2.servers.ServerManager.stop', mock_stop_server)
    @patch('novaclient.v2.servers.ServerManager.get', mock_get_server)
    def test_concurrent_instance(self):
        create_instance('inst-aaa')

        def stop_instance_take_long_time():
            instance_model.stop(project_id_1, ['inst-aaa'])

        def delete_instance_will_hold():
            t1 = time.time()
            try:
                instance_model.delete(project_id_1, ['inst-aaa'])
            except:
                # wait at least 3 seconds for instance to stop.
                # finally we get instance lock.
                # but instance is stopping
                t2 = time.time()
                tools.assert_greater_equal(int(t2 - t1), 3)

        p1 = threading.Thread(target=stop_instance_take_long_time, args=())
        p1.start()
        time.sleep(1)

        p2 = threading.Thread(target=delete_instance_will_hold, args=())
        p2.start()

        p1.join()
        p2.join()

        instance = instance_model.get('inst-aaa')
        tools.eq_(instance['status'], instance_model.INSTANCE_STATUS_STOPPING)

    def test_row_lock(self):
        fixtures.insert_project('proj-aaa')
        fixtures.insert_project('proj-bbb')

        @base.transaction
        def update_project(project_id):
            with base.lock_for_update():
                project = project_model.get(project_id)

            project_model.Project.update(project['id'], qt_vcpus=10)

            time.sleep(3)

        t1 = time.time()
        p1 = threading.Thread(target=update_project, args=('proj-aaa', ))
        p1.start()

        p2 = threading.Thread(target=update_project, args=('proj-bbb', ))
        p2.start()

        p1.join()
        p2.join()

        t2 = time.time()
        # if is table lock, then at least 6 seconds.
        # if is row lock, then at most 4 seconds to finish.
        tools.assert_less_equal(int(t2 - t1), 4)
