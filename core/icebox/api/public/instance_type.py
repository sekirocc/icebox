from densefog import web
import flask   # noqa
from icebox.model.iaas import instance_type as instance_type_model


def describe_instance_types():
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
            'isPublic': {'type': 'boolean'},
            'status': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': [
                        instance_type_model.INSTANCE_TYPE_STATUS_ACTIVE,
                        instance_type_model.INSTANCE_TYPE_STATUS_DELETED,
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'instanceTypeIds': {
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
    instance_type_ids = params.get('instanceTypeIds', None)
    is_public = params.get('isPublic', True)
    status = params.get('status', None)
    search_word = params.get('searchWord', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = instance_type_model.limitation(
        project_ids=[project_id],
        instance_type_ids=instance_type_ids,
        is_public=is_public,
        status=status,
        offset=offset,
        limit=limit,
        search_word=search_word,
        reverse=reverse)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'instanceTypeSet': []
    }
    for instance_type in page['items']:
        formated['instanceTypeSet'].append(instance_type.format())

    return formated
