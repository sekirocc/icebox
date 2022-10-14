from densefog import web
import flask   # noqa
from icebox.api import guard
from icebox.model.iaas import snapshot as snapshot_model
from densefog.model.job import job as job_model


def describe_snapshots():
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
            'searchWord': {'type': ['string', 'null']},
            'snapshotIds': {
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
                        snapshot_model.SNAPSHOT_STATUS_PENDING,
                        snapshot_model.SNAPSHOT_STATUS_ACTIVE,
                        snapshot_model.SNAPSHOT_STATUS_ERROR,
                        snapshot_model.SNAPSHOT_STATUS_DELETED,
                        snapshot_model.SNAPSHOT_STATUS_CEASED,
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
    snapshot_ids = params.get('snapshotIds', None)
    reverse = params.get('reverse', True)
    status = params.get('status', None)

    page = snapshot_model.limitation(project_ids=[project_id],
                                     status=status,
                                     snapshot_ids=snapshot_ids,
                                     search_word=search_word,
                                     offset=offset,
                                     limit=limit,
                                     reverse=reverse)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'snapshotSet': []
    }
    for snapshot in page['items']:
        formated['snapshotSet'].append(snapshot.format())

    return formated


@web.mark_user_operation('snapshot', 'snapshotIds')
@guard.guard_partial_success('snapshotIds')
@guard.guard_project_quota
def create_snapshots():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'volumeId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'count': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 100,
            },
        },
        'required': ['volumeId']
    })

    project_id = flask.request.project['id']
    volume_id = params['volumeId']
    name = params.get('name', '')
    count = params.get('count', 1)

    job_id = snapshot_model.create(project_id=project_id,
                                   volume_id=volume_id,
                                   name=name,
                                   count=count)
    return {
        'jobId': job_id,
        'snapshotIds': job_model.get_resources(job_id)
    }


@web.mark_user_operation('snapshot', 'snapshotIds')
def delete_snapshots():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'snapshotIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['snapshotIds']
    })

    project_id = flask.request.project['id']
    snapshot_ids = params.get('snapshotIds', None)
    snapshot_model.delete(project_id, snapshot_ids)

    return {
        'snapshotIds': snapshot_ids
    }


@web.mark_user_operation('snapshot', 'snapshotId')
def modify_snapshot_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'snapshotId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
        },
        'required': ['snapshotId']
    })

    project_id = flask.request.project['id']
    snapshot_id = params.get('snapshotId')
    name = params.get('name', None)
    description = params.get('description', None)

    snapshot_model.modify(project_id, snapshot_id, name, description)

    return {
        'snapshotId': snapshot_id
    }
