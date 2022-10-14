from keystoneauth1.identity import v3 as keystone_v3
from keystoneauth1 import session as keystone_session
from keystoneclient.v3 import client as keystone_client

from icebox.model.iaas.openstack import constants
from icebox import config


def client(project_id=None):
    if project_id:
        project = {'project_id': project_id}
    else:
        project = {'project_name': 'admin'}

    auth = keystone_v3.Password(username=config.CONF.op_admin_name,
                                password=config.CONF.op_admin_pass,
                                auth_url=config.CONF.op_keystone_endpoint,
                                user_domain_name='default',
                                project_domain_name='default',
                                **project)
    sess = keystone_session.Session(auth=auth)
    client = keystone_client.Client(session=sess)
    return client


def add_user_role(project_id):
    c = client()
    c.roles.grant(
        user=c.users.find(name=config.CONF.op_admin_name),
        role=c.roles.find(name='admin'),
        project=project_id)


def create_project(name):
    c = client()
    t = c.projects.create(name='%s%s' % (constants.NAME_PREFIX, name),
                          domain=c.domains.find(name='default'))
    return {
        'id': t.id,
        'name': t.name,
        'enabled': t.enabled,
        'description': t.description,
    }


def delete_project(project_id):
    c = client()
    c.projects.delete(project=project_id)


def get_project(id):
    c = client()
    t = c.projects.get(id)
    return {
        'id': t.id,
        'name': t.name,
        'enabled': t.enabled,
        'description': t.description,
    }


def list_projects():
    c = client()
    projects = c.projects.list()
    return [{
        'id': t.id,
        'name': t.name,
        'enabled': t.enabled,
        'description': t.description,
    } for t in projects if t.name.startswith(
        constants.NAME_PREFIX)]
