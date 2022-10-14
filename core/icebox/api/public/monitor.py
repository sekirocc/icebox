from densefog import web
import flask   # noqa
import gevent
from gevent.pool import Group
from icebox.model.iaas import monitor as monitor_model


def get_monitor():
    params = web.validate_request({
        'type': 'object',
        'properties': {
            'resourceIds': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'uniqueItems': True
            },
            'metrics': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'minItems': 0,
                'uniqueItems': True
            },
            'period': {'type': 'string'},
        },
        'required': ['resourceIds', 'metrics', 'period'],
    })

    project_id = flask.request.project['id']
    resource_ids = params['resourceIds']
    metrics = params['metrics']
    period = params['period']

    formated = {
        'monitorSet': []
    }

    def get_each_monitor(resource_id,
                         project_id,
                         metric,
                         period):
        monitor = monitor_model.get_monitor(resource_id=resource_id,
                                            project_id=project_id,
                                            metric=metric,
                                            period=period)
        formated['monitorSet'].append(monitor.format())

    group = Group()

    for resource_id in resource_ids:
        for metric in metrics:
            s = gevent.spawn(get_each_monitor,
                             resource_id=resource_id,
                             project_id=project_id,
                             metric=metric,
                             period=period)
            group.add(s)

    group.join()

    return formated
