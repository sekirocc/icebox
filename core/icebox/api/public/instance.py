from densefog import web
import flask   # noqa
from icebox import billing
from densefog.common import utils
from icebox.api import guard
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import image as image_model
from densefog.model.job import job as job_model


def describe_instances():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'limit': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 100,
            },
            'offset': {'type': 'integer', 'minimum': 0},
            'reverse': {'type': 'boolean'},
            'verbose': {'type': 'boolean'},
            'searchWord': {'type': ['string', 'null']},
            'instanceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'status': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': [
                        instance_model.INSTANCE_STATUS_PENDING,
                        instance_model.INSTANCE_STATUS_ACTIVE,
                        instance_model.INSTANCE_STATUS_STARTING,
                        instance_model.INSTANCE_STATUS_STOPPED,
                        instance_model.INSTANCE_STATUS_STOPPING,
                        instance_model.INSTANCE_STATUS_RESTARTING,
                        instance_model.INSTANCE_STATUS_SCHEDULING,
                        instance_model.INSTANCE_STATUS_DELETED,
                        instance_model.INSTANCE_STATUS_CEASED,
                        instance_model.INSTANCE_STATUS_ERROR
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        }
    })

    project_id = flask.request.project['id']
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    search_word = params.get('searchWord', None)
    instance_ids = params.get('instanceIds', None)
    reverse = params.get('reverse', True)
    verbose = params.get('verbose', False)
    status = params.get('status', None)

    page = instance_model.limitation(project_ids=[project_id],
                                     status=status,
                                     instance_ids=instance_ids,
                                     search_word=search_word,
                                     offset=offset,
                                     limit=limit,
                                     reverse=reverse,
                                     verbose=verbose)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'instanceSet': []
    }
    for instance in page['items']:
        instance_formated = instance.format()
        if verbose:
            instance_formated['instanceType'] = instance['instance_type'].format()  # noqa
            instance_formated['image'] = instance['image'].format()
            instance_formated['network'] = instance['network'].format()
            instance_formated['subnet'] = instance['subnet'].format()
            try:
                instance_formated['eip'] = instance['eip'].format()
            except:
                instance_formated['eip'] = None

            instance_formated['volumes'] = [v.format() for v in instance['volumes']]  # noqa

        formated['instanceSet'].append(instance_formated)

    return formated


@web.mark_user_operation('instance', 'instanceIds')
@guard.guard_partial_success('instanceIds')
@guard.guard_project_quota
def create_instances():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'maxLength': 50},
            'imageId': {'type': 'string'},
            'instanceTypeId': {'type': 'string'},
            'subnetId': {'type': 'string'},
            'ipAddress': {'type': 'string'},
            'loginMode': {
                'type': 'string',
                'enum': ['keyPair', 'password']
            },
            'keyPairId': {'type': 'string'},
            'loginPassword': {'type': 'string'},
            'userData': {'type': 'string'},
            'count': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 100,
            },
        },
        'required': ['imageId', 'instanceTypeId', 'subnetId', 'loginMode']
    })
    project_id = flask.request.project['id']

    name = params.get('name', '')

    image_id = params.get('imageId')
    instance_type_id = params.get('instanceTypeId')
    subnet_id = params.get('subnetId')
    ip_address = params.get('ipAddress', None)

    login_mode = params.get('loginMode')
    key_pair_id = params.get('keyPairId', None)
    login_password = params.get('loginPassword', None)

    user_data = params.get('userData', None)

    count = params.get('count', 1)

    job_id = instance_model.create(project_id, name,
                                   image_id=image_id,
                                   instance_type_id=instance_type_id,
                                   login_mode=login_mode,
                                   key_pair_id=key_pair_id,
                                   login_password=login_password,
                                   subnet_id=subnet_id,
                                   ip_address=ip_address,
                                   user_data=user_data,
                                   count=count
                                   )
    instance_ids = job_model.get_resources(job_id)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.instances.create_instances(project_id,
                                                  instance_type_id,
                                                  instance_ids)

    return {
        'jobId': job_id,
        'instanceIds': instance_ids
    }


@web.mark_user_operation('instance', 'instanceIds')
@guard.guard_partial_success('instanceIds')
def start_instances():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        },
        'required': ['instanceIds']
    })

    project_id = flask.request.project['id']
    instance_ids = params['instanceIds']

    job_id = instance_model.start(project_id, instance_ids)

    return {
        'jobId': job_id,
        'instanceIds': instance_ids
    }


@web.mark_user_operation('instance', 'instanceIds')
@guard.guard_partial_success('instanceIds')
def stop_instances():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        },
        'required': ['instanceIds']
    })

    project_id = flask.request.project['id']
    instance_ids = params['instanceIds']

    job_id = instance_model.stop(project_id, instance_ids)

    return {
        'jobId': job_id,
        'instanceIds': instance_ids
    }


@web.mark_user_operation('instance', 'instanceIds')
@guard.guard_partial_success('instanceIds')
def delete_instances():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        },
        'required': ['instanceIds']
    })

    project_id = flask.request.project['id']
    instance_ids = params['instanceIds']

    instance_ids = instance_model.delete(project_id, instance_ids)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.instances.delete_instances(project_id, instance_ids)

    return {
        'instanceIds': instance_ids
    }


@web.mark_user_operation('instance', 'instanceIds')
@guard.guard_partial_success('instanceIds')
def restart_instances():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'restartType': {
                'type': 'string',
                'enum': [
                    instance_model.RESTART_TYPE_HARD,
                    instance_model.RESTART_TYPE_SOFT
                ]
            }
        },
        'required': ['instanceIds']
    })

    project_id = flask.request.project['id']
    instance_ids = params['instanceIds']
    restart_type = params.get('restartType', instance_model.RESTART_TYPE_SOFT)

    job_id = instance_model.restart(project_id, instance_ids, restart_type)

    return {
        'jobId': job_id,
        'instanceIds': instance_ids
    }


@web.mark_user_operation('instance', 'instanceIds')
@guard.guard_partial_success('instanceIds')
def reset_instances():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'loginMode': {
                'type': 'string',
                'enum': ['keyPair', 'password']
            },
            'keyPairId': {'type': 'string'},
            'loginPassword': {'type': 'string'},
            'imageId': {'type': 'string'},
        },
        'required': ['instanceIds']
    })

    project_id = flask.request.project['id']
    instance_ids = params['instanceIds']

    login_mode = params.get('loginMode')
    key_pair_id = params.get('keyPairId', None)
    login_password = params.get('loginPassword', None)

    image_id = params.get('imageId', None)

    job_id = instance_model.reset(project_id,
                                  instance_ids,
                                  login_mode,
                                  key_pair_id,
                                  login_password,
                                  image_id)
    return {
        'jobId': job_id,
        'instanceIds': instance_ids
    }


@web.mark_user_operation('instance', 'instanceIds')
@guard.guard_partial_success('instanceIds')
@guard.guard_project_quota
def resize_instances():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'instanceTypeId': {'type': 'string'}
        },
        'required': ['instanceIds', 'instanceTypeId']
    })

    project_id = flask.request.project['id']
    instance_ids = params['instanceIds']
    instance_type_id = params['instanceTypeId']

    job_id = instance_model.resize(project_id,
                                   instance_ids,
                                   instance_type_id)

    instance_ids = job_model.get_resources(job_id)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.instances.resize_instances(project_id,
                                                  instance_type_id,
                                                  instance_ids)

    return {
        'jobId': job_id,
        'instanceIds': instance_ids
    }


@web.mark_user_operation('instance', 'instanceId')
def capture_instance():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
        },
        'required': ['instanceId']
    })

    project_id = flask.request.project['id']
    instance_id = params.get('instanceId')
    name = params.get('name', '')

    job_id = image_model.create(project_id, instance_id, name)
    image_id = job_model.get_resources(job_id)[0]

    return {
        'jobId': job_id,
        'instanceId': instance_id,
        'imageId': image_id,
    }


@web.mark_user_operation('instance', 'instanceId')
def change_password():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceId': {'type': 'string'},
            'loginPassword': {'type': 'string'},
        },
        'required': ['instanceId', 'loginPassword']
    })

    project_id = flask.request.project['id']
    instance_id = params.get('instanceId')
    login_password = params.get('loginPassword')

    instance_model.change_password(project_id,
                                   instance_id,
                                   login_password)

    return {
        'instanceId': instance_id,
    }


@web.mark_user_operation('instance', 'instanceId')
def change_key_pair():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceId': {'type': 'string'},
            'keyPairId': {'type': 'string'},
        },
        'required': ['instanceId', 'keyPairId']
    })

    project_id = flask.request.project['id']
    instance_id = params.get('instanceId')
    key_pair_id = params.get('keyPairId')

    instance_model.change_key_pair(project_id,
                                   instance_id,
                                   key_pair_id)

    return {
        'instanceId': instance_id,
    }


@web.mark_user_operation('instance', 'instanceId')
def modify_instance_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
        },
        'required': ['instanceId']
    })

    project_id = flask.request.project['id']
    instance_id = params['instanceId']
    name = params.get('name', None)
    description = params.get('description', None)

    instance_model.modify(project_id, instance_id, name, description)

    return {
        'instanceId': instance_id
    }


def connect_vnc():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceId': {'type': 'string'},
        },
        'required': ['instanceId']
    })

    project_id = flask.request.project['id']
    instance_id = params['instanceId']

    vnc = instance_model.connect_vnc(project_id, instance_id)

    return {
        'token': vnc['token'],
        'host': vnc['host'],
        'port': vnc['port']
    }


def get_instance_output():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceId': {'type': 'string'},
        },
        'required': ['instanceId']
    })

    project_id = flask.request.project['id']
    instance_id = params['instanceId']

    output = instance_model.get_output(project_id, instance_id)

    return {
        'output': output,
    }
