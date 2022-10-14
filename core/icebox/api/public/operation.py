from densefog import web
import flask   # noqa
from densefog.model.journal import operation as operation_model


def describe_operations():
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
            'createdStart': {
                'type': 'string',
                'format': 'date-time'
            },
            'createdEnd': {
                'type': 'string',
                'format': 'date-time'
            },
        }
    })

    project_id = flask.request.project['id']
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    created_start = params.get('createdStart', None)
    created_end = params.get('createdEnd', None)
    reverse = params.get('reverse', True)

    page = operation_model.limitation(project_ids=[project_id],
                                      created_start=created_start,
                                      created_end=created_end,
                                      offset=offset,
                                      limit=limit,
                                      reverse=reverse)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'operationSet': []
    }
    for opertn in page['items']:
        formated['operationSet'].append(opertn.format())
    return formated
