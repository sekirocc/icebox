import env  # noqa
import json
import patches
from mock import patch
from nose import tools
from densefog.common import utils
from densefog.model.job import job as job_model
from icebox.model.iaas import eip as eip_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import eip_resource as eip_resource_model
from icebox.model.iaas import error as iaas_error

import fixtures
import fixtures_openstack as op_fixtures

project_id_1 = 'prjct-1234'
network_id_1 = 'network-id-aa'


def create_instance(instance_id, network_id=None):
    rand_id = utils.generate_key(32)
    fixtures.insert_instance_type(project_id=project_id_1, instance_type_id=rand_id)  # noqa
    fixtures.insert_image(project_id=project_id_1, image_id=rand_id)

    if not network_id:
        network_id = utils.generate_key(10)
    subnet_id = utils.generate_key(10)

    fixtures.insert_network(project_id=project_id_1, network_id=network_id)
    fixtures.insert_subnet(project_id=project_id_1,
                           network_id=network_id, subnet_id=subnet_id)
    fixtures.insert_instance(project_id=project_id_1, instance_id=instance_id,
                             network_id=network_id, subnet_id=subnet_id,
                             status=instance_model.INSTANCE_STATUS_ACTIVE)

    # now the instance's network have external gateway.
    network_model.Network.update(network_id, **{
        'external_gateway_ip': '10.10.10.10'
    })

    return instance_id


def mock_create_floatingip(*args, **kwargs):
    return op_fixtures.op_mock_create_floatingip['floatingip']


def mock_nope(*args, **kwargs):
    return True


@patches.nova_authenticate
class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patch('icebox.model.iaas.openstack.api.do_create_floatingip', mock_create_floatingip)  # noqa
    def test_create(self):
        with tools.assert_raises(iaas_error.CreateEipInsufficientFloatingip):
            eip_model.create(project_id=project_id_1, name='eip-aaa', count=1)

        fixtures.insert_floatingip()
        eip_model.create(project_id=project_id_1, name='eip-aaa', count=1)
        tools.eq_(eip_model.limitation()['total'], 1)

    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_rate_limit', mock_nope)   # noqa
    def test_update(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)

        # update bandwidth => 200
        eip_model.update(project_id_1, [eip_id], 200)
        tools.eq_(eip_model.get(eip_id)['bandwidth'], 200)

    def test_delete(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)

        eip_model.delete(project_id_1, [eip_id])
        tools.eq_(eip_model.limitation()['total'], 1)
        tools.eq_(eip_model.get(eip_id)['status'], 'deleted')

    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_port', mock_nope)  # noqa
    def test_associate(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)
        instance_id = create_instance('inst-id-a', network_id=network_id_1)

        # clear the instance's network's gateway
        network_model.Network.update(network_id_1, **{
            'external_gateway_ip': ''
        })

        # so the instance's network will be unreachable. associate failed.
        with tools.assert_raises(iaas_error.AssociateEipWithUnreachableInstance):  # noqa
            eip_model.associate(project_id_1, eip_id, instance_id)

        # now the instance's network have external gateway.
        network_model.Network.update(network_id_1, **{
            'external_gateway_ip': '10.10.10.10'
        })
        # then associate success
        eip_model.associate(project_id_1, eip_id, instance_id)

        eip_resource = eip_resource_model.get(eip_id)
        tools.eq_(eip_resource['resource_id'], instance_id)
        tools.eq_(eip_resource['resource_type'],
                  eip_model.RESOURCE_TYPE_INSTANCE)

        instance_id_b = create_instance('inst-id-b', network_id='network-id-bb')  # noqa
        # eip associated before cannot associate to another instance.
        with tools.assert_raises(iaas_error.EipCanNotAssociate):
            eip_model.associate(project_id_1, eip_id, instance_id_b)

    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_port', mock_nope)  # noqa
    def test_dissociate(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)
        instance_id = create_instance('inst-id-a')

        eip_model.associate(project_id_1, eip_id, instance_id)

        eip_model.dissociate(project_id_1, [eip_id])

        with tools.assert_raises(iaas_error.EipResourceNotFound):
            eip_resource_model.get(eip_id)

        with tools.assert_raises(iaas_error.EipCanNotDissociate):
            eip_model.dissociate(project_id_1, [eip_id])

    @patch('icebox.model.iaas.openstack.api.do_delete_floatingip', mock_nope)  # noqa
    def test_erase(self):
        from densefog.model.job import run_job

        eip_id = fixtures.insert_eip(project_id=project_id_1,
                                     status=eip_model.EIP_STATUS_ACTIVE)

        eip_model.delete(project_id_1, [eip_id])

        job_id = job_model.limitation(
            limit=0, run_at=utils.seconds_later(11))['items'][0]['id']
        run_job(job_id, fixtures.worker)

        tools.assert_equal(bool(eip_model.get(eip_id)['ceased']), True)

    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_port', mock_nope)  # noqa
    def test_limitation(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)

        tools.eq_(eip_model.limitation(project_ids=[project_id_1])['total'], 1)
        tools.eq_(eip_model.limitation(project_ids=[])['total'], 0)

        tools.eq_(eip_model.limitation(status=[eip_model.EIP_STATUS_ACTIVE])['total'], 1)   # noqa
        tools.eq_(eip_model.limitation(status=[eip_model.EIP_STATUS_DELETED])['total'], 0)   # noqa

        tools.eq_(eip_model.limitation(eip_ids=[eip_id])['total'], 1)
        tools.eq_(eip_model.limitation(eip_ids=[])['total'], 0)

        tools.eq_(eip_model.limitation(search_word=eip_id)['total'], 1)

        instance_id = create_instance('inst-id-a', network_id=network_id_1)
        eip_model.associate(project_id_1, eip_id, instance_id)

        eip1 = eip_model.limitation(eip_ids=[eip_id], verbose=False)['items'][0]    # noqa
        tools.eq_(eip1['resource_type'], eip_model.RESOURCE_TYPE_INSTANCE)
        tools.eq_(eip1['resource_id'], instance_id)
        with tools.assert_raises(KeyError):
            tools.ok_(eip1['resource'])

        eip2 = eip_model.limitation(eip_ids=[eip_id], verbose=True)['items'][0]    # noqa
        tools.eq_(eip2['resource_type'], eip_model.RESOURCE_TYPE_INSTANCE)
        tools.eq_(eip2['resource_id'], instance_id)
        tools.eq_(eip2['resource']['id'], instance_id)


@patches.nova_authenticate
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_port', mock_nope)  # noqa
    def test_public_describe_eips(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeEips'
        }))
        data = json.loads(result.data)

        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        tools.eq_(1, len(data['data']['eipSet']))
        tools.eq_(None, data['data']['eipSet'][0]['resourceType'])
        tools.eq_(None, data['data']['eipSet'][0]['resourceId'])
        with tools.assert_raises(KeyError):
            tools.ok_(data['data']['eipSet'][0]['resource'])

        instance_id = create_instance('inst-id-a', network_id=network_id_1)
        eip_model.associate(project_id_1, eip_id, instance_id)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeEips',
            'verbose': True
        }))
        data = json.loads(result.data)

        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        tools.eq_(1, len(data['data']['eipSet']))
        tools.eq_(eip_model.RESOURCE_TYPE_INSTANCE,
                  data['data']['eipSet'][0]['resourceType'])
        tools.eq_(instance_id,
                  data['data']['eipSet'][0]['resourceId'])
        tools.eq_(instance_id,
                  data['data']['eipSet'][0]['resource']['instanceId'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.eips.EipBiller.allocate_eips', mock_nope)  # noqa
    def test_public_describe_eips_with_status(self):
        fixtures.insert_eip(
            project_id=project_id_1, eip_id='eip-aaa',
            status=eip_model.EIP_STATUS_ACTIVE)
        fixtures.insert_eip(
            project_id=project_id_1, eip_id='eip-bbb',
            status=eip_model.EIP_STATUS_DELETED)
        fixtures.insert_eip(
            project_id=project_id_1, eip_id='eip-ccc',
            status=eip_model.EIP_STATUS_ACTIVE)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeEips',
                'status': status
            }))
            return result

        result = send_request([eip_model.EIP_STATUS_ACTIVE])

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.eips.EipBiller.allocate_eips', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_create_floatingip', mock_create_floatingip)  # noqa
    def test_public_allocate_eips(self):
        fixtures.insert_floatingips()

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'AllocateEips',
            'name': 'eip-name',
            'count': 1,
        }))
        eip_ids = json.loads(result.data)['data']['eipIds']

        tools.eq_(eip_model.limitation(
            eip_ids=eip_ids)['total'], 1)

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.eips.EipBiller.allocate_eips', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_create_floatingip', mock_create_floatingip)  # noqa
    def test_public_allocate_eips_with_insufficient(self):
        fixtures.insert_floatingip(floatingip_id='fip-aaa',
                                   ip='10.10.10.11')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'AllocateEips',
            'name': 'eip-name',
            'count': 2,
        }))
        tools.eq_(4761, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.eips.EipBiller.update_bandwidth', mock_nope)  # noqa
    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_rate_limit', mock_nope)   # noqa
    def test_public_update_bandwidth(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'UpdateBandwidth',
            'eipIds': [eip_id],
            'bandwidth': 200,
        }))

        eip_ids = json.loads(result.data)['data']['eipIds']
        tools.eq_(len(eip_ids), 1)
        tools.eq_(eip_ids[0], eip_id)

        eip = eip_model.get(eip_id)
        tools.eq_(eip['bandwidth'], 200)

    @patches.check_access_key(project_id_1)
    @patch('icebox.billing.eips.EipBiller.release_eips', mock_nope)  # noqa
    def test_public_release_eips(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ReleaseEips',
            'eipIds': [eip_id],
        }))
        eip_ids = json.loads(result.data)['data']['eipIds']
        tools.eq_(len(eip_ids), 1)
        tools.eq_(eip_ids[0], eip_id)

        tools.eq_(eip_model.limitation(
            status=[eip_model.EIP_STATUS_DELETED])['total'], 1)

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_port', mock_nope)  # noqa
    def test_public_associate_eip(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)

        network_id = network_id_1
        instance_id = create_instance('inst-id-a', network_id=network_id)

        def send_request():
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'AssociateEip',
                'instanceId': instance_id,
                'eipId': eip_id,
            }))
            return result

        # clear the instance's network's gateway
        network_model.Network.update(network_id_1, **{
            'external_gateway_ip': ''
        })

        result = send_request()
        data = json.loads(result.data)

        # it will be fail because instance's network have no gateway.
        tools.eq_(4701, data['retCode'])
        tools.eq_(eip_id, data['data']['eipId'])
        tools.eq_(network_id, data['data']['networkId'])

        # now the instance's network have external gateway.
        network_model.Network.update(network_id, **{
            'external_gateway_ip': '10.10.10.10'
        })

        result = send_request()
        data = json.loads(result.data)

        # it will be fail because instance's network have no gateway.
        tools.eq_(0, data['retCode'])

        eip_resource = eip_resource_model.get(eip_id)
        tools.eq_(eip_resource['resource_id'], instance_id)
        tools.eq_(eip_resource['resource_type'], eip_model.RESOURCE_TYPE_INSTANCE)  # noqa

    @patches.check_access_key(project_id_1)
    @patch('icebox.model.iaas.openstack.api.do_update_floatingip_port', mock_nope)  # noqa
    def test_public_dissociate_eips(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)
        instance_id = create_instance('inst-id-a')

        eip_model.associate(project_id_1, eip_id, instance_id)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DissociateEips',
            'eipIds': [eip_id],
        }))

        eip_ids = json.loads(result.data)['data']['eipIds']
        tools.eq_(len(eip_ids), 1)
        tools.eq_(eip_ids[0], eip_id)

        with tools.assert_raises(iaas_error.EipResourceNotFound):
            eip_resource_model.get(eip_id)

    @patches.check_access_key(project_id_1)
    def test_modify_eip_attributes(self):
        eip_id = fixtures.insert_eip(project_id=project_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'ModifyEipAttributes',
            'eipId': eip_id,
            'name': 'eip-name',
            'description': 'eip-desc',
        }))
        tools.eq_(0, json.loads(result.data)['retCode'])

        eip = eip_model.limitation(eip_ids=[eip_id])['items'][0]
        tools.eq_(eip['name'], 'eip-name')
        tools.eq_(eip['description'], 'eip-desc')

    @patches.check_manage()
    def test_manage_describe_eips(self):
        fixtures.insert_eip(eip_id='eip_id_1',
                            address='address_1',
                            op_floatingip_id='op_floatingip_id_1')
        fixtures.insert_eip(eip_id='eip_id_2',
                            address='address_2',
                            op_floatingip_id='op_floatingip_id_2')

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeEips'
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])
        tools.eq_(2, len(data['data']['eipSet']))

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeEips',
            'eipIds': ['eip_id_1'],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        eip_set = data['data']['eipSet']
        tools.eq_(1, len(eip_set))
        tools.eq_('eip_id_1', eip_set[0]['eipId'])
        tools.eq_('address_1', eip_set[0]['address'])
        tools.eq_('op_floatingip_id_1', eip_set[0]['opFloatingipId'])

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeEips',
            'eipIds': ['eip_id_1', 'eip_id_2'],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])
        tools.eq_(2, len(data['data']['eipSet']))

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeEips',
            'addresses': ['address_1', 'address_2'],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])
        tools.eq_(2, len(data['data']['eipSet']))

        result = fixtures.manage.post('/', data=json.dumps({
            'action': 'DescribeEips',
            'opFloatingipIds': ['op_floatingip_id_1', 'op_floatingip_id_2'],
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(2, data['data']['total'])
        tools.eq_(2, len(data['data']['eipSet']))
