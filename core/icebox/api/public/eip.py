from densefog import web
import flask   # noqa
from icebox import billing
from densefog.common import utils
from icebox.api import guard
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
            'eipIds': {
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
    eip_ids = params.get('eipIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)
    verbose = params.get('verbose', False)

    page = eip_model.limitation(project_ids=[project_id],
                                status=status,
                                eip_ids=eip_ids,
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
        if verbose:
            try:
                eip_formated['resource'] = eip['resource'].format()
            except:
                eip_formated['resource'] = None

        formated['eipSet'].append(eip_formated)

    return formated


@web.mark_user_operation('eip', 'eipId')
@guard.guard_partial_success('eipIds')
@guard.guard_project_quota
def allocate_eips():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
            'bandwidth': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 300,
            },
            'count': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 100,
            },
        }
    })
    project_id = flask.request.project['id']
    name = params.get('name', '')
    description = params.get('description', '')
    bandwidth = params.get('bandwidth', eip_model.DEFAULT_BANDWIDTH)
    count = params.get('count', 1)

    eip_ids = eip_model.create(project_id,
                               name=name,
                               description=description,
                               bandwidth=bandwidth,
                               count=count)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.eips.allocate_eips(project_id, eip_ids)

    return {
        'eipIds': eip_ids,
    }


@web.mark_user_operation('eip', 'eipIds')
@guard.guard_partial_success('eipIds')
def update_bandwidth():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'eipIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'bandwidth': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 300
            },
        },
        'required': ['eipIds', 'bandwidth']
    })

    project_id = flask.request.project['id']
    eip_ids = params['eipIds']
    bandwidth = params['bandwidth']

    eip_model.update(project_id, eip_ids, bandwidth)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.eips.update_bandwidth(project_id, eip_ids)

    return {
        'eipIds': eip_ids
    }


@web.mark_user_operation('eip', 'eipIds')
def release_eips():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'eipIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['eipIds']
    })
    project_id = flask.request.project['id']
    eip_ids = params['eipIds']
    eip_model.delete(project_id, eip_ids)

    # call billing api. ignore exceptions.
    with utils.silent():
        billing.client.eips.release_eips(project_id, eip_ids)

    return {
        'eipIds': eip_ids
    }


@web.mark_user_operation('eip', 'eipId')
def associate_eip():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'eipId': {'type': 'string'},
            'instanceId': {'type': 'string'},
        },
        'required': ['eipId', 'instanceId']
    })
    project_id = flask.request.project['id']
    eip_id = params['eipId']
    instance_id = params['instanceId']

    eip_model.associate(project_id, eip_id, instance_id)

    return {
        'eipId': eip_id
    }


@web.mark_user_operation('eip', 'eipIds')
@guard.guard_partial_success('eipIds')
def dissociate_eips():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'eipIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['eipIds']
    })
    project_id = flask.request.project['id']
    eip_ids = params['eipIds']

    eip_model.dissociate(project_id, eip_ids)

    return {
        'eipIds': eip_ids
    }


@web.mark_user_operation('eip', 'eipId')
def modify_eip_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'eipId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
        },
        'required': ['eipId']
    })

    project_id = flask.request.project['id']
    eip_id = params.get('eipId')
    name = params.get('name', '')
    description = params.get('description', '')

    eip_model.modify(project_id, eip_id, name, description)

    return {
        'eipId': eip_id
    }
