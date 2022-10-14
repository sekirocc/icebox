from densefog import web
import flask   # noqa
from icebox.model.iaas import subnet as subnet_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import floatingip as fip_model
from icebox.model.iaas import subnet_resource as subres_model


def describe_networks():
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
                        network_model.NETWORK_STATUS_PENDING,
                        network_model.NETWORK_STATUS_ACTIVE,
                        network_model.NETWORK_STATUS_BUILDING,
                        network_model.NETWORK_STATUS_DISABLED,
                        network_model.NETWORK_STATUS_ERROR,
                        network_model.NETWORK_STATUS_DELETED,
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
            'networkIds': {
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
    network_ids = params.get('networkIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)
    verbose = params.get('verbose', False)

    page = network_model.limitation(network_ids=network_ids,
                                    project_ids=project_ids,
                                    status=status,
                                    offset=offset,
                                    limit=limit,
                                    search_word=search_word,
                                    reverse=reverse,
                                    verbose=verbose)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'networkSet': []
    }
    for network in page['items']:
        network_formated = network.format()
        if verbose:
            network_formated['subnets'] = []
            for subnet in network['subnets']:
                network_formated['subnets'].append(subnet.format())
        formated['networkSet'].append(network_formated)

    return formated


def describe_subnets():
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
                        subnet_model.SUBNET_STATUS_ACTIVE,
                        subnet_model.SUBNET_STATUS_DELETED
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
            'subnetIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'networkIds': {
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
    subnet_ids = params.get('subnetIds', None)
    network_ids = params.get('networkIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = subnet_model.limitation(project_ids=project_ids,
                                   status=status,
                                   subnet_ids=subnet_ids,
                                   network_ids=network_ids,
                                   offset=offset,
                                   limit=limit,
                                   search_word=search_word,
                                   reverse=reverse)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'subnetSet': []
    }
    for subnet in page['items']:
        subnet_formated = subnet.format()
        subnet_formated['opSubnetId'] = subnet['op_subnet_id']
        formated['subnetSet'].append(subnet_formated)

    return formated


def add_subnet_resources():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'subnetId': {'type': 'string'},
            'resourceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'resourceType': {
                'type': 'string',
                'enum': [
                    subnet_model.RESOURCE_TYPE_LOAD_BALANCER,
                    subnet_model.RESOURCE_TYPE_SERVER,
                ]
            }
        },
        'required': ['subnetId', 'resourceIds', 'resourceType']
    })

    subnet_id = params.get('subnetId')
    resource_ids = params.get('resourceIds')
    resource_type = params.get('resourceType')

    subres_model.add(subnet_id, resource_ids, resource_type)
    return {
        'resourceIds': resource_ids
    }


def rem_subnet_resources():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'resourceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'resourceType': {
                'type': 'string',
                'enum': [
                    subnet_model.RESOURCE_TYPE_LOAD_BALANCER,
                    subnet_model.RESOURCE_TYPE_SERVER,
                ]
            }
        },
        'required': ['resourceIds', 'resourceType']
    })

    resource_ids = params.get('resourceIds')
    resource_type = params.get('resourceType')

    subres_model.remove(resource_type=resource_type,
                        resource_ids=resource_ids)
    return {
        'resourceIds': resource_ids
    }


def count_floatingips():
    return {
        'count': fip_model.count()
    }


def consume_floatingips():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'addresses': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        },
        'required': ['addresses']
    })

    addresses = params.get('addresses')
    fip_model.consume_ips(addresses)

    return {
        'addresses': addresses
    }


def release_floatingips():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'addresses': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        },
        'required': ['addresses']
    })

    addresses = params.get('addresses')
    fip_model.release_ips(addresses)

    return {
        'addresses': addresses
    }
