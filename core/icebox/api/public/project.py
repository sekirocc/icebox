import flask   # noqa
from icebox.model.project import project as project_model


def describe_quotas():
    project_id = flask.request.project['id']
    project = project_model.get(project_id)

    formated = {
        'total': project.format_total_quota(),
        'usage': project.format_usage_quota(),
    }

    return formated
