import env  # noqa
from nose import tools
from densefog.common import utils
from icebox.model.iaas import eip as eip_model
from icebox.model.iaas import eip_resource as eip_resource_model
from icebox.model.iaas import error as iaas_error

import fixtures

project_id_1 = 'prjct-1234'


def create_instance(instance_id):
    rand_id = utils.generate_key(32)
    fixtures.insert_instance_type(project_id=project_id_1, instance_type_id=rand_id)  # noqa
    fixtures.insert_image(project_id=project_id_1, image_id=rand_id)
    fixtures.insert_network(project_id=project_id_1, network_id=rand_id)
    fixtures.insert_subnet(project_id=project_id_1, subnet_id=rand_id)
    fixtures.insert_instance(project_id=project_id_1, instance_id=instance_id)
    return instance_id


class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_create(self):
        eip_resource_model.create(
            eip_id='eip-aaa',
            resource_id='inst-aaa',
            resource_type=eip_model.RESOURCE_TYPE_INSTANCE)

        eip_resource = eip_resource_model.get(eip_id='eip-aaa')
        tools.eq_(eip_resource['eip_id'], 'eip-aaa')
        tools.eq_(eip_resource['resource_id'], 'inst-aaa')
        tools.eq_(eip_resource['resource_type'], eip_model.RESOURCE_TYPE_INSTANCE)   # noqa

    def test_delete(self):
        fixtures.insert_eip_resource(
            eip_id='eip-aaa',
            resource_id='inst-aaa',
            resource_type=eip_model.RESOURCE_TYPE_INSTANCE)

        eip_resource_model.delete(eip_id='eip-aaa')
        with tools.assert_raises(iaas_error.EipResourceNotFound):
            eip_resource_model.get(eip_id='eip-aaa')

    def test_relations(self):
        fixtures.insert_eip(project_id=project_id_1, eip_id='eip-aaa')
        create_instance('inst-aaa')

        eip_resource_model.create(
            eip_id='eip-aaa',
            resource_id='inst-aaa',
            resource_type=eip_model.RESOURCE_TYPE_INSTANCE)

        fixtures.insert_eip(project_id=project_id_1, eip_id='eip-bbb')
        create_instance('inst-bbb')

        eip_rels_2 = eip_resource_model.relations_from_instances(
            ['inst-aaa', 'inst-bbb'])

        # {instance_id: eip_id}
        tools.eq_(len(eip_rels_2.items()), 2)
        tools.eq_(eip_rels_2['inst-aaa'], 'eip-aaa')
        tools.eq_(eip_rels_2['inst-bbb'], None)

        instance_rels_2 = eip_resource_model.relations_from_eips(
            ['eip-aaa', 'eip-bbb'])

        # {eip_id: (resource_type, resource_id)}
        tools.eq_(len(instance_rels_2.items()), 2)
        tools.eq_(instance_rels_2['eip-aaa'][0],
                  eip_model.RESOURCE_TYPE_INSTANCE)
        tools.eq_(instance_rels_2['eip-aaa'][1],
                  'inst-aaa')

        tools.eq_(instance_rels_2['eip-bbb'][0], None)
        tools.eq_(instance_rels_2['eip-bbb'][1], None)
