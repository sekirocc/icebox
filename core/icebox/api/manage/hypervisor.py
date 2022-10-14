from densefog import web
from icebox.model.iaas import hypervisor as hypervisor_model


def describe_hypervisors():
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
            'status': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': [
                        hypervisor_model.HYPERVISOR_STATUS_ENABLED,
                        hypervisor_model.HYPERVISOR_STATUS_DISABLED,
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'states': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': [
                        hypervisor_model.HYPERVISOR_STATE_UP,
                        hypervisor_model.HYPERVISOR_STATE_DOWN,
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'hostnames': {
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

    limit = params.get('limit', 20)
    offset = params.get('offset', 0)
    reverse = params.get('reverse', True)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    states = params.get('states', None)
    names = params.get('names', None)

    page = hypervisor_model.limitation(
        limit=limit,
        offset=offset,
        reverse=reverse,
        search_word=search_word,
        status=status,
        states=states,
        names=names)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'hypervisorSet': []
    }
    for hypervisor in page['items']:
        formated['hypervisorSet'].append(hypervisor.format())

    return formated


def sync_hypervisors():
    hypervisor_model.sync_all()


def modify_hypervisor_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'hypervisorId': {'type': 'string'},
            'name': {'type': 'string'},
            'description': {'type': 'string'},
        },
        'required': ['hypervisorId']
    })

    hypervisor_id = params['hypervisorId']
    name = params.get('name', None)
    description = params.get('description', None)

    hypervisor_model.modify(hypervisor_id,
                            name=name,
                            description=description)
