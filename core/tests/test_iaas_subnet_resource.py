import env  # noqa
from nose import tools
from icebox.model.iaas import subnet as subnet_model
from icebox.model.iaas import subnet_resource as subres_model

import fixtures

project_id_1 = 'prjct-1234'
subnet_id_1 = 'sbn-1234'


class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)
        network_id = fixtures.insert_network(project_id=project_id_1)
        fixtures.insert_subnet(
            subnet_id=subnet_id_1,
            project_id=project_id_1, network_id=network_id,
            cidr='192.168.200.0/24')

    def test_add(self):
        load_balancers = ['lb-1', 'lb-2', 'lb-3']
        servers = ['svr-1', 'svr-2']
        subres_model.add(
            subnet_id=subnet_id_1,
            resource_ids=load_balancers,
            resource_type=subnet_model.RESOURCE_TYPE_LOAD_BALANCER)

        subres_model.add(
            subnet_id=subnet_id_1,
            resource_ids=servers,
            resource_type=subnet_model.RESOURCE_TYPE_SERVER)

        page = subres_model.limitation(subnet_ids=[subnet_id_1])['items']
        tools.eq_(5, len(page))

        page = subres_model.limitation(
            subnet_ids=[subnet_id_1],
            resource_type=subnet_model.RESOURCE_TYPE_LOAD_BALANCER)['items']
        tools.eq_(3, len(page))

        page = subres_model.limitation(
            subnet_ids=[subnet_id_1],
            resource_type=subnet_model.RESOURCE_TYPE_SERVER)['items']
        tools.eq_(2, len(page))

    def test_remove(self):
        load_balancers = ['lb-1', 'lb-2', 'lb-3']
        servers = ['svr-1', 'svr-2']

        fixtures.insert_subnet_resources(
            subnet_id=subnet_id_1,
            resource_ids=load_balancers,
            resource_type=subnet_model.RESOURCE_TYPE_LOAD_BALANCER)
        # insert 5 resources, 3 lb, 2 servers
        fixtures.insert_subnet_resources(
            subnet_id=subnet_id_1,
            resource_ids=servers,
            resource_type=subnet_model.RESOURCE_TYPE_SERVER)

        # delete 3 lb
        subres_model.remove(
            resource_ids=['lb-1', 'lb-2', 'lb-3'],
            resource_type=subnet_model.RESOURCE_TYPE_LOAD_BALANCER)

        # left 2 resources
        page = subres_model.limitation(subnet_ids=[subnet_id_1])['items']
        tools.eq_(2, len(page))

        # delete 1 servers.
        subres_model.remove(
            resource_ids=['svr-1'],
            resource_type=subnet_model.RESOURCE_TYPE_SERVER)

        # left 1 resources
        page = subres_model.limitation(subnet_ids=[subnet_id_1])['items']
        tools.eq_(1, len(page))

    def test_count(self):
        load_balancers = ['lb-1', 'lb-2', 'lb-3']
        servers = ['svr-1', 'svr-2']

        # insert 5 resources, 3 lb, 2 servers
        fixtures.insert_subnet_resources(
            subnet_id=subnet_id_1,
            resource_ids=load_balancers,
            resource_type=subnet_model.RESOURCE_TYPE_LOAD_BALANCER)
        fixtures.insert_subnet_resources(
            subnet_id=subnet_id_1,
            resource_ids=servers,
            resource_type=subnet_model.RESOURCE_TYPE_SERVER)

        tools.eq_(5, subres_model.count(subnet_id=subnet_id_1))
        tools.eq_(3, subres_model.count(
            subnet_id=subnet_id_1,
            resource_type=subnet_model.RESOURCE_TYPE_LOAD_BALANCER))
        tools.eq_(2, subres_model.count(
            subnet_id=subnet_id_1,
            resource_type=subnet_model.RESOURCE_TYPE_SERVER))
