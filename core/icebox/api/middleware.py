import flask
import functools

from icebox import config

from icebox.model.project import access_key as access_key_model
from icebox.model.project import project as project_model
from icebox.model.project import error as project_error

from densefog import logger
logger = logger.getChild(__file__)


def _load_access_key():
    key = flask.request.headers.get('X-Ice-Key')
    secret = flask.request.headers.get('X-Ice-Secret')
    flask.request.key = key
    flask.request.secret = secret

    logger.info('load access key: %s' % flask.request.key)


def _load_project():
    project_id = access_key_model.check(
        flask.request.key,
        flask.request.secret,
        flask.request.params)

    flask.request.project_id = project_id
    logger.info('load project_id: %s' % flask.request.project_id)

    flask.request.project = project_model.get(project_id)


def load_access_key(method):
    @functools.wraps(method)
    def wrap(*args, **kwargs):
        _load_access_key()
        return method(*args, **kwargs)
    return wrap


def load_project(method):
    @functools.wraps(method)
    def wrap(*args, **kwargs):
        _load_project()
        return method(*args, **kwargs)
    return wrap


def _check_manage():
    if not flask.request.key or \
       not flask.request.secret or \
       not flask.request.key == config.CONF.manage_key or \
       not flask.request.secret == config.CONF.manage_secret:
        raise project_error.ManageAccessKeyInvalid(flask.request.key)


def check_manage(method):
    @functools.wraps(method)
    def wrap(*args, **kwargs):
        _check_manage()
        return method(*args, **kwargs)
    return wrap
