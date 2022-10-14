from densefog import web
import flask   # noqa
from icebox.model.iaas import eip as eip_model


def describe_eips():
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
            'status': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': [
                        eip_model.EIP_STATUS_ACTIVE,
                        eip_model.EIP_STATUS_ASSOCIATED,
                        eip_model.EIP_STATUS_DELETED
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'searchWord': {'type': ['string', 'null']},
            'projectIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'eipIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'addresses': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'opFloatingipIds': {
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

    project_ids = params.get('projectIds', None)
    eip_ids = params.get('eipIds', None)
    addresses = params.get('addresses', None)
    op_floatingip_ids = params.get('opFloatingipIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)
    verbose = params.get('verbose', False)

    page = eip_model.limitation(project_ids=project_ids,
                                status=status,
                                eip_ids=eip_ids,
                                addresses=addresses,
                                op_floatingip_ids=op_floatingip_ids,
                                verbose=verbose,
                                offset=offset,
                                limit=limit,
                                search_word=search_word,
                                reverse=reverse)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'eipSet': []
    }
    for eip in page['items']:
        eip_formated = eip.format()
        eip_formated['opFloatingipId'] = eip['op_floatingip_id']
        if verbose:
            try:
                eip_formated['resource'] = eip['resource'].format()
            except:
                eip_formated['resource'] = None

        formated['eipSet'].append(eip_formated)

    return formated
