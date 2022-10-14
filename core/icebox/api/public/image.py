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
            'isPublic': {'type': 'boolean'},
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
                    ],
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

    project_id = flask.request.project['id']
    image_ids = params.get('imageIds', None)
    search_word = params.get('searchWord', None)
    status = params.get('status', None)
    is_public = params.get('isPublic', False)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = image_model.limitation(
        project_ids=[project_id],
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


@web.mark_user_operation('image', 'imageIds')
def delete_images():
    params = web.validate_request({
        'type': 'object',
        'properties': {
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

    project_id = flask.request.project['id']
    image_ids = params['imageIds']

    image_model.delete(project_id, image_ids)

    return {
        'imageIds': image_ids
    }


@web.mark_user_operation('image', 'imageId')
def modify_image_attributes():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'imageId': {'type': 'string'},
            'name': {'type': 'string', 'maxLength': 50},
            'description': {'type': 'string', 'maxLength': 250}
        },
        'required': ['imageId']
    })

    project_id = flask.request.project['id']
    image_id = params.get('imageId')
    name = params.get('name', None)
    description = params.get('description', None)

    image_model.modify(project_id,
                       image_id,
                       name=name,
                       description=description)

    return {
        'imageId': image_id
    }
