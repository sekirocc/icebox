import env  # noqa
import patches
from mock import patch
import fixtures
import json
from nose import tools
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import port_forwarding as port_forwarding_model
from icebox.model.iaas import network as network_model

project_id_1 = 'tnnt-1234'


def mock_port_forwarding(*args, **kwargs):
    return {
        u'id': u'92c8a704-2902-457a-94e6-5abe29438e23',
        u'inside_addr': u'10.148.200.200',
        u'inside_port': 9999,
        u'outside_port': 19999,
        u'protocol': u'tcp',
        u'router_id': u'df450f29-777f-4cf1-9688-4b4e06529dcd'
    }


def mock_nope(*args, **kwargs):
    return True


@patches.nova_authenticate
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('icebox.model.iaas.openstack.api.do_add_port_forwarding', mock_port_forwarding)   # noqa
    def test_create(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)

        # there is no subnet in the network. so indside_address is useless
        with tools.assert_raises(iaas_error.PortForwardingInsideAddressNotInSubnetsError):   # noqa
            port_forwarding_model.create(
                project_id=project_id_1,
                network_id=network_id,
                protocol='tcp',
                outside_port=80,
                inside_address='192.168.100.1',
                inside_port=80)

        # add a subnet in it.
        fixtures.insert_subnet(project_id=project_id_1,
                               network_id=network_id,
                               cidr='192.168.100.0/24',
                               ip_start='192.168.100.1',
                               ip_end='192.168.100.254')

        port_forwarding_id = port_forwarding_model.create(
            project_id=project_id_1,
            network_id=network_id,
            protocol='tcp',
            outside_port=80,
            inside_address='192.168.100.1',
            inside_port=80)

        tools.eq_(port_forwarding_model.limitation()['total'], 1)
        return port_forwarding_id

    @patch('icebox.model.iaas.openstack.api.do_add_port_forwarding', mock_port_forwarding)   # noqa
    def test_create_outside_port_used(self):
        network_id = fixtures.insert_network(
            project_id=project_id_1,
            status=network_model.NETWORK_STATUS_ACTIVE)
        # add a subnet in it.
        fixtures.insert_subnet(project_id=project_id_1,
                               network_id=network_id,
                               cidr='192.168.100.0/24',
                               ip_start='192.168.100.1',
                               ip_end='192.168.100.254')

        # create two port forwarding with the same outside_port
        port_forwarding_model.create(
            project_id=project_id_1,
            network_id=network_id,
            protocol='tcp',
            outside_port=80,
            inside_address='192.168.100.1',
            inside_port=8080)
        with tools.assert_raises(iaas_error.PortForwardingOutsidePortUsedError):  # noqa
            port_forwarding_model.create(
                project_id=project_id_1,
                network_id=network_id,
                protocol='tcp',
                outside_port=80,
                inside_address='192.168.100.1',
                inside_port=7070)

    def test_get(self):
        port_forwarding_id = self.test_create()
        port_forwarding = port_forwarding_model.get(
            port_forwarding_id=port_forwarding_id)

        tools.eq_(port_forwarding.protocol, 'tcp')

        with tools.assert_raises(iaas_error.PortForwardingNotFound):
            port_forwarding = port_forwarding_model.get(
                port_forwarding_id='pf-123')

    def test_limitation(self):
        port_forwarding_id = fixtures.insert_port_forwarding(
            project_id=project_id_1, port_forwarding_id='pf-aaa',
            inside_address='192.168.100.100',
            status=port_forwarding_model.PORT_FORWARDING_STATUS_ACTIVE)

        tools.eq_(port_forwarding_model.limitation(
            project_ids=[project_id_1])['total'], 1)
        tools.eq_(port_forwarding_model.limitation(
            project_ids=[])['total'], 0)

        tools.eq_(port_forwarding_model.limitation(
            status=[
                port_forwarding_model.PORT_FORWARDING_STATUS_ACTIVE
            ])['total'], 1)
        tools.eq_(port_forwarding_model.limitation(
            status=[
                port_forwarding_model.PORT_FORWARDING_STATUS_DELETED
            ])['total'], 0)

        port_forwarding = port_forwarding_model.get(
            port_forwarding_id=port_forwarding_id)

        tools.eq_(port_forwarding_model.limitation(
            network_ids=[port_forwarding['network_id']])['total'], 1)
        tools.eq_(port_forwarding_model.limitation(
            network_ids=[])['total'], 0)

        tools.eq_(port_forwarding_model.limitation(
            port_forwarding_ids=[port_forwarding_id])['total'], 1)
        tools.eq_(port_forwarding_model.limitation(
            port_forwarding_ids=[])['total'], 0)

        tools.eq_(port_forwarding_model.limitation(
            search_word=port_forwarding_id)['total'], 1)
        tools.eq_(port_forwarding_model.limitation(
            search_word='192.168.100')['total'], 1)
        tools.eq_(port_forwarding_model.limitation(
            search_word='192.168.100.10')['total'], 1)
        tools.eq_(port_forwarding_model.limitation(
            search_word='192.168.100.100')['total'], 1)

        tools.eq_(port_forwarding_model.limitation(
            search_word='192.168.200')['total'], 0)
        tools.eq_(port_forwarding_model.limitation(
            search_word='192.168.200.100')['total'], 0)

    def test_delete(self):
        port_forwarding_id = self.test_create()
        port_forwarding_model.delete(
            project_id=project_id_1,
            port_forwarding_ids=[port_forwarding_id])

        tools.eq_(port_forwarding_model.limitation()['total'], 1)
        port_forwarding = port_forwarding_model.get(
            port_forwarding_id=port_forwarding_id)
        tools.eq_(port_forwarding['status'],
                  port_forwarding_model.PORT_FORWARDING_STATUS_DELETED)

    @patch('icebox.model.iaas.openstack.api.do_remove_port_forwarding', mock_nope)   # noqa
    def test_erase(self):
        pf_id = fixtures.insert_port_forwarding(
            status=port_forwarding_model.PORT_FORWARDING_STATUS_DELETED)

        port_forwarding_model.erase(pf_id)

        tools.assert_equal(bool(port_forwarding_model.get(pf_id)['ceased']),
                           True)


@patches.nova_authenticate
@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_public_describe_port_forwardings(self):
        fixtures.insert_port_forwarding(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribePortForwardings'
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(1, json.loads(result.data)['data']['total'])

    def test_public_describe_port_forwardings_with_search_word(self):
        fixtures.insert_port_forwarding(port_forwarding_id='pf-123',
                                        inside_address='192.168.200.200',
                                        project_id=project_id_1)

        def send_request(search_word):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribePortForwardings',
                'searchWord': search_word
            }))
            return result

        result = send_request('pf-123')
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(1, json.loads(result.data)['data']['total'])

        result = send_request('192.168.200.2')
        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(1, json.loads(result.data)['data']['total'])

    def test_public_describe_port_forwardings_with_status(self):
        fixtures.insert_port_forwarding(
            project_id=project_id_1, port_forwarding_id='pf-aaa',
            status=port_forwarding_model.PORT_FORWARDING_STATUS_ACTIVE)
        fixtures.insert_port_forwarding(
            project_id=project_id_1, port_forwarding_id='pf-bbb',
            status=port_forwarding_model.PORT_FORWARDING_STATUS_ACTIVE)
        fixtures.insert_port_forwarding(
            project_id=project_id_1, port_forwarding_id='pf-ccc',
            status=port_forwarding_model.PORT_FORWARDING_STATUS_DELETED)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribePortForwardings',
                'status': status
            }))
            return result

        result = send_request([port_forwarding_model.PORT_FORWARDING_STATUS_ACTIVE])  # noqa

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    @patch('icebox.model.iaas.openstack.api.do_add_port_forwarding', mock_port_forwarding)   # noqa
    def test_public_create_port_forwarding(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_ACTIVE)

        fixtures.insert_subnet(project_id=project_id_1,
                               network_id='net-aaa',
                               cidr='192.168.100.0/24',
                               ip_start='192.168.100.1',
                               ip_end='192.168.100.254')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'CreatePortForwarding',
            'networkId': 'net-aaa',
            'protocol': 'tcp',
            'outsidePort': 80,
            'insideAddress': '192.168.100.1',
            'insidePort': 8080
        }))

        tools.eq_(0, json.loads(result.data)['retCode'])

        data = json.loads(result.data)['data']

        tools.assert_not_equal(data['portForwardingId'], None)

    def test_public_delete_port_forwarding(self):
        fixtures.insert_network(project_id=project_id_1, network_id='net-aaa',
                                status=network_model.NETWORK_STATUS_ACTIVE)

        port_forwarding_id = fixtures.insert_port_forwarding(
            network_id='net-aaa',
            project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DeletePortForwardings',
            'portForwardingIds': [port_forwarding_id],
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        tools.eq_(port_forwarding_model.limitation(
            status=[
                port_forwarding_model.PORT_FORWARDING_STATUS_DELETED
            ])['total'], 1)

    def test_modify_port_forwarding_attributes(self):
        port_forwarding_id = fixtures.insert_port_forwarding(
            project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ModifyPortForwardingAttributes',
            'portForwardingId': port_forwarding_id,
            'name': 'new-name',
            'description': 'new-description'
        }))
        pf_id = json.loads(result.data)['data']['portForwardingId']
        tools.eq_(pf_id, port_forwarding_id)

        port_forwarding = port_forwarding_model.get(port_forwarding_id)
        tools.eq_(port_forwarding['name'], 'new-name')
        tools.eq_(port_forwarding['description'], 'new-description')
