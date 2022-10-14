from densefog import web
import flask   # noqa
from icebox.model.iaas import image as image_model


def describe_images():
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
                        image_model.IMAGE_STATUS_PENDING,
                        image_model.IMAGE_STATUS_ACTIVE,
                        image_model.IMAGE_STATUS_DELETED,
                        image_model.IMAGE_STATUS_CEASED,
                        image_model.IMAGE_STATUS_ERROR,
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
            'imageIds': {
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
    image_ids = params.get('imageIds', None)

    # for manage api, we add additional param: projectIds
    # with which we can get multiple projects' private images at once.
    project_ids = params.get('projectIds', None)

    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    is_public = params.get('isPublic', False)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = image_model.limitation(
        project_ids=project_ids,
        image_ids=image_ids,
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
        'imageSet': []
    }
    for image in page['items']:
        formated['imageSet'].append(image.format())

    return formated


def sync_images():
    image_model.sync_all()


def modify_image_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'projectId': {'type': 'string'},
            'imageId': {'type': 'string'},
            'name': {'type': 'string'},
            'description': {'type': 'string'},
            'osFamily': {'type': 'string'},
            'platform': {'type': 'string'},
            'processorType': {'type': 'string'},
        },
        'required': ['imageId']
    })

    image_id = params['imageId']
    project_id = image_model.PUBLIC_IMAGE
    name = params.get('name', None)
    description = params.get('description', None)
    os_family = params.get('osFamily', None)
    platform = params.get('platform', None)
    processor_type = params.get('processorType', None)

    image_model.modify(project_id,
                       image_id,
                       name=name,
                       description=description,
                       os_family=os_family,
                       platform=platform,
                       processor_type=processor_type)


def delete_images():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'projectId': {'type': 'string'},
            'imageIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 20,
                'uniqueItems': True
            }
        },
        'required': ['imageIds']
    })

    image_ids = params['imageIds']
    project_id = params.get('projectId', image_model.PUBLIC_IMAGE)

    image_model.delete(project_id, image_ids)

    return {
        'imageIds': image_ids
    }
