from densefog import web
import flask   # noqa
from icebox.model.project import project as project_model
from icebox.model.project import access_key as access_key_model
from icebox.model.project import error as project_error


def create_access_keys():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'accessKeySet': {
                'type': 'array',
                'items': {
                    'projectId': {'type': 'string'},
                    'accessKey': {'type': 'string'},
                    'accessSecret': {'type': 'string'},
                    'expireAt': {
                        'type': ['string', 'null'],
                        'format': 'date-time'
                    },
                },
                'required': ['projectId', 'accessKey', 'accessSecret']
            }
        },
        'required': ['accessKeySet']
    })

    for access_key_params in params['accessKeySet']:
        project_id = access_key_params['projectId']
        access_key = access_key_params['accessKey']
        access_secret = access_key_params['accessSecret']
        expire_at = access_key_params.get('expireAt', None)

        access_key_model.create(
            project_id=project_id,
            key=access_key,
            secret=access_secret,
            expire_at=expire_at)

    return {}


def delete_access_keys():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'accessKeySet': {
                'type': 'array',
                'items': {
                    'projectId': {'type': 'string'},
                    'accessKey': {'type': 'string'},
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['accessKeySet']
    })

    for access_key_params in params['accessKeySet']:
        project_id = access_key_params['projectId']
        access_key = access_key_params['accessKey']

        access_key_model.delete(
            project_id=project_id,
            keys=[access_key])

    return {}


def upsert_quota():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'quotaSet': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'projectId': {'type': 'string'},
                        'quota': {
                            'type': 'object',
                            'properties': {
                                'instances': {'type': 'integer'},
                                'vCPUs': {'type': 'integer'},
                                'memory': {'type': 'integer'},
                                'images': {'type': 'integer'},
                                'eIPs': {'type': 'integer'},
                                'networks': {'type': 'integer'},
                                'volumes': {'type': 'integer'},
                                'volumeSize': {'type': 'integer'},
                                'snapshots': {'type': 'integer'},
                                'keyPairs': {'type': 'integer'},
                                'loadBalancers': {'type': 'integer'},
                            },
                            'required': [
                                'instances',
                                'vCPUs',
                                'memory',
                                'images',
                                'eIPs',
                                'networks',
                                'volumes',
                                'volumeSize',
                                'snapshots',
                                'keyPairs',
                            ]
                        }
                    },
                    'required': [
                        'projectId',
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        },
        'required': [
            'quotaSet',
        ]
    })

    for quota_set in params['quotaSet']:
        project_id = quota_set['projectId']
        qt_instances = quota_set['quota']['instances']
        qt_vcpus = quota_set['quota']['vCPUs']
        qt_memory = quota_set['quota']['memory']
        qt_images = quota_set['quota']['images']
        qt_eips = quota_set['quota']['eIPs']
        qt_networks = quota_set['quota']['networks']
        qt_volumes = quota_set['quota']['volumes']
        qt_volume_size = quota_set['quota']['volumeSize']
        qt_snapshots = quota_set['quota']['snapshots']
        qt_key_pairs = quota_set['quota']['keyPairs']

        try:
            project_model.get(project_id)
            project_model.update(project_id,
                                 qt_instances=qt_instances,
                                 qt_vcpus=qt_vcpus,
                                 qt_memory=qt_memory,
                                 qt_images=qt_images,
                                 qt_eips=qt_eips,
                                 qt_networks=qt_networks,
                                 qt_volumes=qt_volumes,
                                 qt_volume_size=qt_volume_size,
                                 qt_snapshots=qt_snapshots,
                                 qt_key_pairs=qt_key_pairs)
        except project_error.ProjectNotFound:
            project_model.create(project_id,
                                 qt_instances=qt_instances,
                                 qt_vcpus=qt_vcpus,
                                 qt_memory=qt_memory,
                                 qt_images=qt_images,
                                 qt_eips=qt_eips,
                                 qt_networks=qt_networks,
                                 qt_volumes=qt_volumes,
                                 qt_volume_size=qt_volume_size,
                                 qt_snapshots=qt_snapshots,
                                 qt_key_pairs=qt_key_pairs)
    return {}
