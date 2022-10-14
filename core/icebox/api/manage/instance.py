from densefog import web
import flask   # noqa
from icebox.model.iaas import instance as instance_model


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
            'projectIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'instanceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'names': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'opServerIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        }
    })

    project_ids = params.get('projectIds', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    search_word = params.get('searchWord', None)
    instance_ids = params.get('instanceIds', None)
    names = params.get('names', None)
    op_server_ids = params.get('opServerIds', None)
    reverse = params.get('reverse', True)
    verbose = params.get('verbose', False)
    status = params.get('status', None)

    page = instance_model.limitation(project_ids=project_ids,
                                     status=status,
                                     instance_ids=instance_ids,
                                     names=names,
                                     op_server_ids=op_server_ids,
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
        instance_formated['opServerId'] = instance['op_server_id']
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
