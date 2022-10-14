import env  # noqa
import patches
import json
import copy
from mock import patch
from nose import tools
from densefog.common import utils
from densefog.common.utils import MockObject
from icebox.model.iaas import image as image_model
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import error as iaas_error
from densefog.model.job import job as job_model
import fixtures


def mock_wait_snapshot(*args, **kwargs):
    pass


def mock_wait_capshot(*args, **kwargs):
    pass


def mock_nope(*args, **kwargs):
    return True


def mock_image(*args, **kwargs):
    pass


project_id_1 = 'curr-prjct-123'


class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)
        self.image_id = fixtures.insert_image(project_id=project_id_1)

        fixtures.insert_instance_type(project_id=project_id_1)
        fixtures.insert_network(project_id=project_id_1)
        fixtures.insert_subnet(project_id=project_id_1)
        self.instance_id = fixtures.insert_instance(
            project_id=project_id_1,
            instance_id='inst-abcd',
            status=instance_model.INSTANCE_STATUS_ACTIVE)

    def test_create(self):
        job_id = image_model.create(project_id_1, 'inst-abcd', 'cool-image-a')

        image_id = job_model.get_resources(job_id)[0]
        img = image_model.get(image_id)
        # after create we get a dummy image
        tools.ok_(img['op_image_id'].startswith('dummy'))
        # for now, size is still 0, and is pending
        tools.eq_(img['size'], 0)
        tools.eq_(img['status'], image_model.IMAGE_STATUS_PENDING)
        # some attributes inherit from original instance image.
        instance_img = image_model.get(self.image_id)
        tools.eq_(img['platform'], instance_img['platform'])
        tools.eq_(img['os_family'], instance_img['os_family'])
        tools.eq_(img['processor_type'], instance_img['processor_type'])
        tools.eq_(img['min_vcpus'], instance_img['min_vcpus'])

        page = image_model.limitation(is_public=False)
        tools.eq_(len(page['items']), 2)

        # create image result in two jobs. one for instance, one for image
        jobs = job_model.limitation(limit=0)['items']
        action_set = set([job['action'] for job in jobs])
        tools.eq_(action_set, set(['CaptureInstances', 'CreateImage']))

    @patch('icebox.model.iaas.openstack.api.do_nova_create_image')
    @patch('icebox.model.iaas.waiter.wait_snapshot_available')
    @patch('icebox.model.iaas.openstack.api.do_create_capshot')
    @patch('icebox.model.iaas.waiter.wait_capshot_available')
    @patch('icebox.model.iaas.openstack.api.do_glance_create_image')
    @patch('icebox.model.iaas.openstack.api.do_delete_image')
    @patch('icebox.model.iaas.openstack.api.do_delete_snapshot')
    def test_create_image(self,
                          do_delete_snapshot, do_delete_image,
                          do_glance_create_image,
                          wait_capshot_available, do_create_capshot,
                          wait_snapshot_available, do_nova_create_image):
        mock1 = MockObject(**copy.copy(fixtures.op_mock_image))
        mock1.block_device_mapping = json.dumps([{'snapshot_id': 's-123'}])
        do_nova_create_image.return_value = mock1

        mock2 = MockObject(**copy.copy(fixtures.op_mock_snapshot))
        mock2.status = 'available'
        wait_snapshot_available.return_value = mock2

        mock3 = MockObject(**copy.copy(fixtures.op_mock_capshot))
        do_create_capshot.return_value = mock3

        mock4 = MockObject(**copy.copy(fixtures.op_mock_capshot))
        mock4.status = 'available'
        wait_capshot_available.return_value = mock4

        mock5 = MockObject(**copy.copy(fixtures.op_mock_image))
        do_glance_create_image.return_value = mock5

        # insert unfinished image
        fixtures.insert_image(project_id=project_id_1,
                              image_id='img-1234',
                              op_image_id='dummp-1234',
                              status=image_model.IMAGE_STATUS_PENDING)
        image_model.create_image('img-1234', self.instance_id)

        img = image_model.get('img-1234')
        tools.eq_(img['size'], mock4['size'] * (1024 ** 3))
        tools.eq_(img['op_image_id'], mock5['id'])
        # inherit min_disk, min_memory from nova created image.
        # TODO, really?
        tools.eq_(img['min_disk'], mock1['min_disk'])
        tools.eq_(img['min_memory'], mock1['min_memory'])
        tools.eq_(img['status'], image_model.IMAGE_STATUS_ACTIVE)

        tools.eq_(do_delete_image.called, True)
        tools.eq_(do_delete_snapshot.called, True)

    def test_get(self):
        fixtures.insert_image(
            image_id='image_id_1',
            image_name='coolname',
            status=image_model.IMAGE_STATUS_ACTIVE)

        image = image_model.get('image_id_1')
        tools.eq_(image['name'], 'coolname')
        tools.eq_(image['status'], image_model.IMAGE_STATUS_ACTIVE)

    def test_limitation(self):
        fixtures.insert_image(image_id='image_id_a')
        fixtures.insert_image(image_id='image_id_b')
        fixtures.insert_image(image_id='image_id_c', project_id=image_model.PUBLIC_IMAGE)   # noqa

        # remember we have a self.image_id inserted by setUp
        tools.eq_(image_model.limitation(is_public=False)['total'], 4)
        tools.eq_(image_model.limitation(is_public=True)['total'], 1)

    def test_delete(self):
        image_id_0 = fixtures.insert_image(project_id=project_id_1,
                                           image_id='image_id_a')
        fixtures.insert_instance(project_id=project_id_1,
                                 image_id=image_id_0,
                                 instance_id='inst_id_a')

        image_id_1 = fixtures.insert_image(project_id=project_id_1,
                                           image_id='img-abcd')
        image_id_2 = fixtures.insert_image(project_id='other-project',
                                           image_id='img-efgh')
        image_id_3 = fixtures.insert_image(project_id=image_model.PUBLIC_IMAGE,
                                           image_id='img-xyzd')

        with tools.assert_raises(iaas_error.DeleteImagesWhenInstanceExists):
            image_model.delete(project_id_1, [image_id_0])

        with tools.assert_raises(iaas_error.ImageNotFound):
            image_model.delete(project_id_1, ['some-other-image'])

        with tools.assert_raises(iaas_error.ResourceNotBelongsToProject):
            image_model.delete(project_id_1, [image_id_2])

        try:
            image_model.delete(image_model.PUBLIC_IMAGE, [image_id_3])
        except iaas_error.ResourceNotBelongsToProject:
            raise Exception('delete public image. shoudnot raise Exception.')

        image_model.delete(project_id_1, [image_id_1])
        tools.eq_(image_model.get('img-abcd')['status'],
                  image_model.IMAGE_STATUS_DELETED)

    @patch('icebox.model.iaas.openstack.api.do_delete_image', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_get_image')
    @patch('icebox.model.iaas.openstack.api.do_delete_capshot')
    def test_erase_capshot_image(self, do_delete_capshot, do_get_image):
        mock = MockObject(**fixtures.op_image_example)
        mock.capshot_id = utils.generate_key(36)
        do_get_image.return_value = mock

        do_delete_capshot.return_value = None

        fixtures.insert_image(project_id=project_id_1,
                              image_id='img-abcd',
                              os_family=image_model.OS_UNKNOWN,
                              status=image_model.IMAGE_STATUS_DELETED)

        image_model.erase('img-abcd')

        tools.eq_(do_delete_capshot.called, True)
        tools.eq_(image_model.get('img-abcd')['status'],
                  image_model.IMAGE_STATUS_CEASED)

    @patch('icebox.model.iaas.openstack.api.do_delete_image', mock_nope)
    @patch('icebox.model.iaas.openstack.api.do_get_image')
    @patch('icebox.model.iaas.openstack.api.do_delete_capshot')
    def test_erase_normal_image(self, do_delete_capshot, do_get_image):
        mock = MockObject(**fixtures.op_image_example)
        mock.capshot_id = None
        do_get_image.return_value = mock
        do_delete_capshot.return_value = None

        fixtures.insert_image(project_id=project_id_1,
                              image_id='img-toerase',
                              op_image_id=utils.generate_key(36),
                              os_family=image_model.OS_UNKNOWN,
                              status=image_model.IMAGE_STATUS_DELETED)

        image_model.erase('img-toerase')

        tools.eq_(do_delete_capshot.called, False)
        tools.eq_(image_model.get('img-toerase')['status'],
                  image_model.IMAGE_STATUS_CEASED)

    def test_modify(self):
        image_id_1 = fixtures.insert_image(project_id=project_id_1,
                                           image_id='img-tomodify',
                                           op_image_id=utils.generate_key(36),
                                           os_family=image_model.OS_UNKNOWN)

        image_model.modify(project_id_1, image_id_1, os_family=image_model.OS_CENTOS)   # noqa

        tools.eq_(image_model.get(image_id_1)['os_family'],
                  image_model.OS_CENTOS)

    @patch('icebox.model.iaas.openstack.api.do_list_images')
    def test_sync_all(self, mock_list_images):
        mock1 = MockObject(**fixtures.op_image_example)
        mock1.id = utils.generate_key(36)
        mock2 = MockObject(**fixtures.op_image_example)
        mock2.id = utils.generate_key(36)
        mock_list_images.return_value = [mock1, mock2]

        image_model.sync_all()

        images = image_model.limitation(limit=0)['items']
        image_ids = [i['op_image_id'] for i in images]
        tools.ok_(mock1.id in image_ids)
        tools.ok_(mock2.id in image_ids)

    @patch('icebox.model.iaas.openstack.api.do_get_image')
    def test_sync(self, mock_get_image):
        fixtures.insert_image(project_id=project_id_1,
                              image_id='img-aaa',
                              os_family=image_model.OS_UNKNOWN,
                              status=image_model.IMAGE_STATUS_PENDING)
        mock = MockObject(**fixtures.op_image_example)
        mock.id = utils.generate_key(36)
        mock.size = 20
        mock.min_disk = 40
        mock.min_memory = 1024
        mock_get_image.return_value = mock

        image_model.sync('img-aaa')

        tools.eq_(image_model.get('img-aaa')['size'], 20)
        tools.eq_(image_model.get('img-aaa')['min_disk'], 40)
        tools.eq_(image_model.get('img-aaa')['min_memory'], 1024)


@patches.nova_authenticate
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    @patches.check_access_key(project_id_1)
    def test_public_describe_images(self):
        image_id_1 = fixtures.insert_image(image_id='img-abc',
                                           project_id=project_id_1)
        image_id_2 = fixtures.insert_image(image_id='img-hig',
                                           project_id=image_model.PUBLIC_IMAGE)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeImages',
            'isPublic': False,
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        # describeImage get only 'mine' images.
        tools.eq_(data['data']['imageSet'][0]['imageId'], image_id_1)

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeImages',
            'isPublic': True,
        }))
        data = json.loads(result.data)
        tools.eq_(0, data['retCode'])
        tools.eq_(1, data['data']['total'])
        # describeImage get only 'public' images.
        tools.eq_(data['data']['imageSet'][0]['imageId'], image_id_2)

    @patches.check_access_key(project_id_1)
    def test_public_describe_images_with_status(self):
        fixtures.insert_image(
            project_id=project_id_1, image_id='img-AAA',
            status=image_model.IMAGE_STATUS_ACTIVE)
        fixtures.insert_image(
            project_id=project_id_1, image_id='img-BBB',
            status=image_model.IMAGE_STATUS_ACTIVE)
        fixtures.insert_image(
            project_id=project_id_1, image_id='img-CCC',
            status=image_model.IMAGE_STATUS_DELETED)

        def send_request(status):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DescribeImages',
                'status': status
            }))
            return result

        result = send_request([image_model.IMAGE_STATUS_ACTIVE])

        tools.eq_(0, json.loads(result.data)['retCode'])
        tools.eq_(2, json.loads(result.data)['data']['total'])

        result = send_request(['unkown-status'])
        tools.eq_(4110, json.loads(result.data)['retCode'])

    @patches.check_access_key(project_id_1)
    def test_public_delete_images(self):
        image_id_1 = fixtures.insert_image(image_id='image_id_1',
                                           project_id=project_id_1)

        image_id_0 = fixtures.insert_image()
        fixtures.insert_instance(project_id=project_id_1, instance_id='inst-abcd')  # noqa

        def send_reuqest(image_id):
            result = fixtures.public.post('/', data=json.dumps({
                'action': 'DeleteImages',
                'imageIds': [image_id]
            }))
            return result

        # delete image with instance using the image
        result = send_reuqest(image_id_0)
        data = json.loads(result.data)
        tools.eq_(data['retCode'], 4771)

        result = send_reuqest(image_id_1)
        data = json.loads(result.data)
        tools.eq_(data['retCode'], 0)
        tools.eq_(data['data']['imageIds'][0], image_id_1)

        tools.eq_(image_model.get(image_id_1)['status'],
                  image_model.IMAGE_STATUS_DELETED)

    @patches.check_access_key(project_id_1)
    def test_public_modify_image(self):
        fixtures.insert_image(image_id='img-aaa',
                              project_id=project_id_1)

        def send_reuqest(image_id, name=None, description=None):
            params = {
                'action': 'ModifyImageAttributes',
                'imageId': image_id
            }
            if name:
                params['name'] = name
            if description:
                params['description'] = description

            result = fixtures.public.post('/', data=json.dumps(params))
            return result

        send_reuqest('img-aaa', name='new-name')
        image = image_model.get('img-aaa')
        tools.eq_(image['name'], 'new-name')

        send_reuqest('img-aaa', description='new-description')
        image = image_model.get('img-aaa')
        tools.eq_(image['description'], 'new-description')

    @patches.check_manage()
    def test_manage_modify_image(self):
        fixtures.insert_image(image_id='img-aaa',
                              project_id=image_model.PUBLIC_IMAGE)

        def send_reuqest(image_id,
                         os_family=None,
                         processor_type=None,
                         platform=None):
            params = {
                'action': 'ModifyImageAttributes',
                'imageId': image_id
            }
            if os_family:
                params['osFamily'] = os_family
            if processor_type:
                params['processorType'] = processor_type
            if platform:
                params['platform'] = platform

            result = fixtures.manage.post('/', data=json.dumps(params))
            return result

        send_reuqest('img-aaa', os_family=image_model.OS_CENTOS)
        image = image_model.get('img-aaa')
        tools.eq_(image['os_family'], image_model.OS_CENTOS)

        send_reuqest('img-aaa', processor_type=image_model.PROCESSOR_TYPE_64)
        image = image_model.get('img-aaa')
        tools.eq_(image['processor_type'], image_model.PROCESSOR_TYPE_64)

        send_reuqest('img-aaa', platform=image_model.PLATFORM_LINUX)
        image = image_model.get('img-aaa')
        tools.eq_(image['platform'], image_model.PLATFORM_LINUX)
