from densefog import web
import flask   # noqa
from icebox.api import guard
from icebox.model.iaas import key_pair as key_pair_model


def describe_key_pairs():
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
            'status': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': [
                        key_pair_model.KEY_PAIR_STATUS_ACTIVE,
                        key_pair_model.KEY_PAIR_STATUS_DELETED,
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'searchWord': {'type': ['string', 'null']},
            'keyPairIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        }
    })

    project_id = flask.request.project['id']
    key_pair_ids = params.get('keyPairIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = key_pair_model.limitation(key_pair_ids=key_pair_ids,
                                     project_ids=[project_id],
                                     status=status,
                                     offset=offset,
                                     limit=limit,
                                     search_word=search_word,
                                     reverse=reverse)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'keyPairSet': []
    }
    for key_pair in page['items']:
        formated['keyPairSet'].append(key_pair.format())

    return formated


@web.mark_user_operation('keyPair', 'keyPairId')
@guard.guard_project_quota
def create_key_pair():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
            'publicKey': {'type': 'string'},
        },
    })
    project_id = flask.request.project['id']
    name = params.get('name', '')
    description = params.get('description', '')
    public_key = params.get('publicKey', None)
    key_pair_id, private_key = key_pair_model.create(project_id,
                                                     name=name,
                                                     description=description,
                                                     public_key=public_key)
    return {
        'keyPairId': key_pair_id,
        'privateKey': private_key
    }


@web.mark_user_operation('keyPair', 'keyPairIds')
def delete_key_pairs():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'keyPairIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['keyPairIds']
    })
    project_id = flask.request.project['id']
    key_pair_ids = params['keyPairIds']
    key_pair_model.delete(project_id, key_pair_ids)

    return {
        'keyPairIds': key_pair_ids
    }


@web.mark_user_operation('keyPair', 'keyPairId')
def modify_key_pair_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'keyPairId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
        },
        'required': ['keyPairId']
    })

    project_id = flask.request.project['id']
    key_pair_id = params.get('keyPairId')
    name = params.get('name', '')
    description = params.get('description', '')

    key_pair_model.modify(project_id, key_pair_id, name, description)

    return {
        'keyPairId': key_pair_id
    }
