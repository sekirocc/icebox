from densefog import web
import flask   # noqa
from icebox.api import guard
from icebox.model.iaas import network as network_model
from icebox.model.iaas import subnet as subnet_model
from icebox.model.iaas import port_forwarding as port_forwarding_model
from densefog.model.job import job as job_model


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

    project_id = flask.request.project['id']
    network_ids = params.get('networkIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)
    verbose = params.get('verbose', False)

    page = network_model.limitation(network_ids=network_ids,
                                    project_ids=[project_id],
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


@web.mark_user_operation('network', 'networkId')
def create_network():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
            'cidr': {'type': 'string'},
        }
    })

    project_id = flask.request.project['id']
    name = params.get('name', '')
    description = params.get('description', '')
    cidr = params.get('cidr', None)

    job_id = network_model.create(project_id,
                                  name=name, description=description)
    network_id = job_model.get_resources(job_id)[0]
    if cidr:
        subnet_model.create(project_id, network_id, cidr=cidr)

    return {
        'jobId': job_id,
        'networkId': network_id,
    }


@web.mark_user_operation('network', 'networkIds')
def delete_networks():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'networkIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['networkIds'],
    })

    project_id = flask.request.project['id']
    network_ids = params['networkIds']
    network_model.delete(project_id, network_ids=network_ids)

    return {
        'networkIds': network_ids
    }


@web.mark_user_operation('network', 'networkId')
def modify_network_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'networkId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
        },
        'required': ['networkId']
    })

    project_id = flask.request.project['id']
    network_id = params.get('networkId')
    name = params.get('name', '')
    description = params.get('description', '')

    network_model.modify(project_id, network_id, name, description)

    return {
        'networkId': network_id
    }


@web.mark_user_operation('network', 'networkIds')
@guard.guard_partial_success('networdIds')
def set_external_gateway():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'bandwidth': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 300,
            },
            'networkIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['networkIds'],
    })

    project_id = flask.request.project['id']
    network_ids = params['networkIds']
    bandwidth = params.get('bandwidth', network_model.DEFAULT_BANDWIDTH)

    network_model.set_external_gateway(project_id,
                                       network_ids=network_ids,
                                       bandwidth=bandwidth)

    return {
        'networkIds': network_ids
    }


@web.mark_user_operation('network', 'networkIds')
@guard.guard_partial_success('networdIds')
def update_external_gateway_bandwidth():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'bandwidth': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 300,
            },
            'networkIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['networkIds', 'bandwidth'],
    })

    project_id = flask.request.project['id']
    network_ids = params['networkIds']
    bandwidth = params.get('bandwidth')

    # invoke the same api as set. because openstack provider the same api
    # for set and update external gateway.
    network_model.set_external_gateway(project_id,
                                       network_ids=network_ids,
                                       bandwidth=bandwidth)

    return {
        'networkIds': network_ids
    }


@web.mark_user_operation('network', 'networkIds')
@guard.guard_partial_success('networdIds')
def unset_external_gateway():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'networkIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['networkIds'],
    })

    project_id = flask.request.project['id']
    network_ids = params['networkIds']

    network_model.unset_external_gateway(project_id,
                                         network_ids=network_ids)

    return {
        'networkIds': network_ids
    }


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
                        subnet_model.SUBNET_STATUS_DELETED,
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'searchWord': {'type': ['string', 'null']},
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

    project_id = flask.request.project['id']
    subnet_ids = params.get('subnetIds', None)
    network_ids = params.get('networkIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = subnet_model.limitation(subnet_ids=subnet_ids,
                                   network_ids=network_ids,
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
        'subnetSet': []
    }
    for subnet in page['items']:
        formated['subnetSet'].append(subnet.format())
    return formated


@web.mark_user_operation('subnet', 'subnetId')
def create_subnet():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'networkId': {'type': 'string'},
            'cidr': {'type': 'string'},
        },
        'required': ['networkId', 'cidr'],
    })

    project_id = flask.request.project['id']
    network_id = params['networkId']
    cidr = params['cidr']

    subnet_id = subnet_model.create(project_id,
                                    network_id,
                                    cidr=cidr)
    return {
        'subnetId': subnet_id
    }


@web.mark_user_operation('subnet', 'subnetIds')
def delete_subnets():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'subnetIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['subnetIds']
    })

    project_id = flask.request.project['id']
    subnet_ids = params['subnetIds']

    subnet_model.delete(project_id,
                        subnet_ids=subnet_ids)

    return {
        'subnetIds': subnet_ids
    }


@web.mark_user_operation('subnet', 'subnetId')
def modify_subnet_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'subnetId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
        },
        'required': ['subnetId']
    })

    project_id = flask.request.project['id']
    subnet_id = params.get('subnetId')
    name = params.get('name', None)
    description = params.get('description', None)

    subnet_model.modify(project_id, subnet_id, name, description)

    return {
        'subnetId': subnet_id
    }


def describe_port_forwardings():
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
                        port_forwarding_model.PORT_FORWARDING_STATUS_ACTIVE,
                        port_forwarding_model.PORT_FORWARDING_STATUS_DELETED,
                    ]
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'searchWord': {'type': ['string', 'null']},
            'networkIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
            'portForwardingIds': {
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
    network_ids = params.get('networkIds', None)
    port_forwarding_ids = params.get('portForwardingIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = port_forwarding_model.limitation(
        network_ids=network_ids,
        project_ids=[project_id],
        port_forwarding_ids=port_forwarding_ids,
        status=status,
        offset=offset,
        limit=limit,
        reverse=reverse,
        search_word=search_word)

    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'portForwardingSet': []
    }
    for port_forwarding in page['items']:
        formated['portForwardingSet'].append(port_forwarding.format())

    return formated


@web.mark_user_operation('portForwarding', 'portForwardingId')
def create_port_forwarding():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'networkId': {'type': 'string'},
            'protocol': {
                'type': 'string',
                'enum': ['tcp', 'udp'],
            },
            'outsidePort': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535,
            },
            'insideAddress': {'type': 'string'},
            'insidePort': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535,
            },
        },
        'required': [
            'networkId',
            'protocol',
            'outsidePort',
            'insideAddress',
            'insidePort'
        ],
    })

    project_id = flask.request.project['id']
    network_id = params['networkId']
    protocol = params['protocol']
    outside_port = params['outsidePort']
    inside_address = params['insideAddress']
    inside_port = params['insidePort']

    port_forwarding_id = port_forwarding_model.create(
        project_id=project_id,
        network_id=network_id,
        protocol=protocol,
        outside_port=outside_port,
        inside_address=inside_address,
        inside_port=inside_port)

    return {
        'portForwardingId': port_forwarding_id,
    }


@web.mark_user_operation('portForwarding', 'portForwardingIds')
def delete_port_forwardings():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'portForwardingIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            },
        },
        'required': ['portForwardingIds'],
    })

    project_id = flask.request.project['id']
    port_forwarding_ids = params['portForwardingIds']

    port_forwarding_model.delete(project_id,
                                 port_forwarding_ids=port_forwarding_ids)
    return {
        'portForwardingIds': port_forwarding_ids
    }


@web.mark_user_operation('portForwarding', 'portForwardingId')
def modify_port_forwarding_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'portForwardingId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250},
        },
        'required': ['portForwardingId']
    })

    project_id = flask.request.project['id']
    port_forwarding_id = params.get('portForwardingId')
    name = params.get('name', None)
    description = params.get('description', None)

    port_forwarding_model.modify(project_id,
                                 port_forwarding_id,
                                 name,
                                 description)

    return {
        'portForwardingId': port_forwarding_id
    }
