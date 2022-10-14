import env  # noqa
from nose import tools
from densefog.common import utils
from icebox.model.iaas import instance_volume as instance_volume_model
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
        instance_volume_model.create(
            volume_id='volume-aaa',
            instance_id='inst-aaa')

        instance_volume = instance_volume_model.get(volume_id='volume-aaa')
        tools.eq_(instance_volume['volume_id'], 'volume-aaa')
        tools.eq_(instance_volume['instance_id'], 'inst-aaa')

    def test_delete(self):
        fixtures.insert_instance_volume(
            volume_id='volume-aaa',
            instance_id='inst-aaa')

        instance_volume_model.delete(volume_id='volume-aaa')
        with tools.assert_raises(iaas_error.InstanceVolumeNotFound):
            instance_volume_model.get(volume_id='volume-aaa')

    def test_relations(self):
        volume_id = fixtures.insert_volume(volume_id='volume-aaa',
                                           project_id=project_id_1)
        instance_id = create_instance('inst-aaa')

        instance_volume_model.create(
            volume_id=volume_id,
            instance_id=instance_id)

        volume_id_2 = fixtures.insert_volume(volume_id='volume-bbb',
                                             project_id=project_id_1)
        instance_id_2 = create_instance('inst-bbb')

        volume_rels_2 = instance_volume_model.relations_from_instances(
            [instance_id, instance_id_2])

        # {instance_id: [volume_id]}
        tools.eq_(len(volume_rels_2.items()), 2)
        tools.eq_(volume_rels_2[instance_id][0], volume_id)
        tools.eq_(len(volume_rels_2[instance_id_2]), 0)

        # volume_id is attached to instance_id
        # volume_id_2 is not attached to any instance
        instance_rels_2 = instance_volume_model.relations_from_volumes(
            [volume_id, volume_id_2])

        tools.eq_(len(instance_rels_2.items()), 2)
        tools.eq_(instance_rels_2[volume_id], instance_id)

        tools.eq_(instance_rels_2[volume_id_2], None)
