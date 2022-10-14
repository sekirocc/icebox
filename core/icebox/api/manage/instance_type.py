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
            'isPublic': {'type': ['boolean', 'null']},
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
            'projectIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
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

    instance_type_ids = params.get('instanceTypeIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    is_public = params.get('isPublic', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = instance_type_model.limitation(
        instance_type_ids=instance_type_ids,
        is_public=is_public,
        offset=offset,
        status=status,
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


def generate_instance_types():
    instance_type_model.generate()


def create_instance_type():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'projectId': {'type': 'string'},
            'vcpus': {'type': 'integer'},
            'memory': {'type': 'integer'},
            'disk': {'type': 'integer'},
        },
        'required': ['vcpus', 'memory', 'disk']
    })

    project_id = params.get('projectId',
                            instance_type_model.PUBLIC_INSTANCE_TYPE)
    vcpus = params['vcpus']
    memory = params['memory']
    disk = params['disk']

    instance_type_id = instance_type_model.create(
        project_id=project_id,
        vcpus=vcpus,
        memory=memory,
        disk=disk)

    return {
        'instanceTypeId': instance_type_id
    }


def delete_instance_types():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'projectId': {'type': 'string'},
            'instanceTypeIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        },
        'required': ['instanceTypeIds']
    })

    instance_type_ids = params['instanceTypeIds']
    project_id = params.get('projectId',
                            instance_type_model.PUBLIC_INSTANCE_TYPE)

    instance_type_model.delete(project_id, instance_type_ids)

    return {
        'instanceTypeIds': instance_type_ids
    }
