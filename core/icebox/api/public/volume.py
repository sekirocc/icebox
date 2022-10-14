from densefog import web
import flask   # noqa
from icebox import billing
from densefog.common import utils
from icebox.api import guard
from icebox.model.iaas import volume as volume_model
from densefog.model.job import job as job_model


def describe_volumes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'limit': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 100,
            },
            'verbose': {'type': 'boolean'},
            'offset': {'type': 'integer', 'minimum': 0},
            'reverse': {'type': 'boolean'},
            'searchWord': {'type': ['string', 'null']},
            'volumeIds': {
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
                        volume_model.VOLUME_STATUS_PENDING,
                        volume_model.VOLUME_STATUS_ACTIVE,
                        volume_model.VOLUME_STATUS_ATTACHING,
                        volume_model.VOLUME_STATUS_DETACHING,
                        volume_model.VOLUME_STATUS_IN_USE,
                        volume_model.VOLUME_STATUS_BACKING_UP,
                        volume_model.VOLUME_STATUS_RESTORING_BACKUP,
                        volume_model.VOLUME_STATUS_DELETED,
                        volume_model.VOLUME_STATUS_CEASED,
                        volume_model.VOLUME_STATUS_ERROR,
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
    volume_ids = params.get('volumeIds', None)
    reverse = params.get('reverse', True)
    verbose = params.get('verbose', False)
    status = params.get('status', None)

    page = volume_model.limitation(project_ids=[project_id],
                                   status=status,
                                   volume_ids=volume_ids,
                                   verbose=verbose,
                                   search_word=search_word,
                                   offset=offset,
                                   limit=limit,
                                   reverse=reverse)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'volumeSet': []
    }
    for volume in page['items']:
        volume_formated = volume.format()
        if verbose:
            try:
                volume_formated['instance'] = volume['instance'].format()
            except:
                volume_formated['instance'] = None

        formated['volumeSet'].append(volume_formated)

    return formated


@web.mark_user_operation('volume', 'volumeIds')
@guard.guard_partial_success('volumeIds')
@guard.guard_project_quota
def create_volumes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'maxLength': 50},
            'count': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 100,
            },
            'snapshotId': {'type': 'string'},
            'size': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 1024,
            },
            'volumeType': {'type': 'string'},
        }
    })
    # option 1: snapshotId
    # option 2: size & volumeType

    project_id = flask.request.project['id']
    snapshot_id = params.get('snapshotId', None)
    size = params.get('size', None)
    name = params.get('name', '')
    count = params.get('count', 1)
    volume_type = params.get('volumeType', None)

    job_id = volume_model.create(project_id=project_id,
                                 snapshot_id=snapshot_id,
                                 size=size,
                                 name=name,
                                 volume_type=volume_type,
                                 count=count)
    volume_ids = job_model.get_resources(job_id)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.volumes.create_volumes(project_id, volume_ids)

    return {
        'jobId': job_id,
        'volumeIds': volume_ids
    }


@web.mark_user_operation('volume', 'volumeIds')
def delete_volumes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'volumeIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['volumeIds']
    })

    project_id = flask.request.project['id']
    volume_ids = params.get('volumeIds', None)
    volume_model.delete(project_id, volume_ids)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.volumes.delete_volumes(project_id, volume_ids)

    return {
        'volumeIds': volume_ids
    }


@web.mark_user_operation('volume', 'volumeId')
@guard.guard_partial_success('volumeIds')
def attach_volume():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceId': {'type': 'string'},
            'volumeId': {'type': 'string'}
        },
        'required': ['instanceId', 'volumeId']
    })

    project_id = flask.request.project['id']
    volume_id = params.get('volumeId')
    instance_id = params.get('instanceId')

    job_id = volume_model.attach(project_id,
                                 volume_id,
                                 instance_id)
    return {
        'jobId': job_id,
        'volumeId': volume_id
    }


@web.mark_user_operation('volume', 'volumeIds')
@guard.guard_partial_success('volumeIds')
def detach_volumes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'instanceId': {'type': 'string'},
            'volumeIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['instanceId', 'volumeIds']
    })

    project_id = flask.request.project['id']
    volume_ids = params.get('volumeIds')
    instance_id = params.get('instanceId')

    job_id = volume_model.detach(project_id,
                                 volume_ids,
                                 instance_id)
    return {
        'jobId': job_id,
        'volumeIds': job_model.get_resources(job_id)
    }


@web.mark_user_operation('volume', 'volumeIds')
@guard.guard_partial_success('volumeIds')
@guard.guard_project_quota
def extend_volumes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'size': {'type': 'integer', 'maximum': 1024},
            'volumeIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['size', 'volumeIds']
    })

    project_id = flask.request.project['id']
    volume_ids = params.get('volumeIds')
    new_size = params.get('size')

    job_id = volume_model.extend(project_id,
                                 volume_ids,
                                 new_size)
    volume_ids = job_model.get_resources(job_id)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.volumes.resize_volumes(project_id, volume_ids)

    return {
        'jobId': job_id,
        'volumeIds': volume_ids
    }


@web.mark_user_operation('volume', 'volumeId')
def modify_volume_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'volumeId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
        },
        'required': ['volumeId']
    })

    project_id = flask.request.project['id']
    volume_id = params.get('volumeId')
    name = params.get('name', None)
    description = params.get('description', None)

    volume_model.modify(project_id, volume_id, name, description)

    return {
        'volumeId': volume_id
    }
