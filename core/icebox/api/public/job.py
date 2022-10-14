from densefog import web
import flask   # noqa
from densefog.model.job import job as job_model


def describe_jobs():
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
                        job_model.JOB_STATUS_PENDING,
                        job_model.JOB_STATUS_RUNNING,
                        job_model.JOB_STATUS_FINISHED,
                        job_model.JOB_STATUS_ERROR,
                    ]
                },
                'minItems': 0,
                'maxItems': 10,
                'uniqueItems': True
            },
            'jobIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'maxItems': 10,
                'uniqueItems': True
            }
        }
    })

    project_id = flask.request.project['id']
    job_ids = params.get('jobIds', None)
    status = params.get('status', None)
    offset = params.get('offset', 0)
    limit = params.get('limit', 20)
    reverse = params.get('reverse', True)

    page = job_model.limitation(project_ids=[project_id],
                                job_ids=job_ids,
                                status=status,
                                offset=offset,
                                limit=limit,
                                reverse=reverse)
    formated = {
        'limit': page['limit'],
        'offset': page['offset'],
        'total': page['total'],
        'jobSet': []
    }
    for job in page['items']:
        formated['jobSet'].append(job.format())

    return formated
