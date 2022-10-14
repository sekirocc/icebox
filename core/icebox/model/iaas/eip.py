from icebox import model
import datetime
import traceback

from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from densefog.model.job import job as job_model

from icebox.model.project import project as project_model
from icebox.model.iaas import eip_resource as eip_resource_model
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import floatingip as floatingip_model
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas.openstack import api as op_api

from densefog import logger
logger = logger.getChild(__file__)

EIP_STATUS_ACTIVE = 'active'
EIP_STATUS_ASSOCIATED = 'associated'
EIP_STATUS_DELETED = 'deleted'

DEFAULT_BANDWIDTH = 1

EMPTY_RESOURCE_ID = utils.encode_uuid(
    '00000000-0000-0000-0000-000000000000')

RESOURCE_TYPE_NONE = 'none'
RESOURCE_TYPE_INSTANCE = 'instance'


class Eip(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.eip

    def status_deletable(self):
        return self['status'] in [
            EIP_STATUS_ACTIVE,
        ]

    def status_associable(self):
        return self['status'] in [
            EIP_STATUS_ACTIVE
        ]

    def status_dissociable(self):
        return self['status'] in [
            EIP_STATUS_ASSOCIATED
        ]

    def format(self):
        formated = {
            'eipId': self['id'],
            'projectId': self['project_id'],
            'name': self['name'],
            'description': self['description'],
            'bandwidth': self['bandwidth'],
            'status': self['status'],
            'address': self['address'],
            'updated': self['updated'],
            'created': self['created'],
            'deleted': self['deleted'],
        }
        try:
            formated['resourceType'] = self['resource_type']
        except:
            formated['resourceType'] = None

        try:
            formated['resourceId'] = self['resource_id']
        except:
            formated['resourceId'] = None

        return formated


def _pre_create(project, count):
    project.must_have_enough_quota('eips', count)

    active_floatingips = floatingip_model.count()
    if active_floatingips < count:
        raise iaas_error.CreateEipInsufficientFloatingip(count,
                                                         active_floatingips)


def create(project_id, name='', description='', bandwidth=DEFAULT_BANDWIDTH,
           count=1):
    """
    acquire project lock
    """
    logger.info('.create() begin, total count: %s' % count)

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        _pre_create(project, count)

        # assume creations all success
        project.consume_quota('eips', count)

    createds = []
    addresses = []
    exceptions = []
    for i in range(count):
        eip_id = 'eip-%s' % utils.generate_key(8)
        try:
            provider_eip = op_api.do_create_floatingip(
                project['op_project_id'], rate_limit=bandwidth)
        except Exception as e:
            exceptions.append({
                'eip': None,
                'exception': e
            })
        else:
            ip = provider_eip['floating_ip_address']
            Eip.insert(**{
                'id': eip_id,
                'project_id': project_id,
                'name': name,
                'description': description,
                'bandwidth': bandwidth,
                'status': EIP_STATUS_ACTIVE,
                'address': ip,
                'op_floatingip_id': provider_eip['id'],
                'updated': datetime.datetime.utcnow(),
                'created': datetime.datetime.utcnow(),
            })
            createds.append(eip_id)
            addresses.append(ip)

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)
        # release those failed.
        project.release_quota('eips', len(exceptions))

    logger.info('.create() OK. createds: %s, exceptions: %s' %
                (len(createds), len(exceptions)))

    floatingip_model.consume_ips(addresses)

    return model.actions_result(createds,
                                exceptions)


def _pre_update(project_id, eip_ids):
    """
    eip should be active,
    """
    eips = []
    for eip_id in eip_ids:
        with base.lock_for_update():
            eip = get(eip_id)

        eip.must_belongs_project(project_id)
        eips.append(eip)

    return eips


@base.transaction
def update(project_id, eip_ids, bandwidth):
    """
    acquire eip lock
    """
    logger.info('.update() begin, total count: %s' % len(eip_ids))

    eips = _pre_update(project_id, eip_ids)

    updateds = []
    exceptions = []
    for eip in eips:
        eip_id = eip['id']
        try:
            op_api.do_update_floatingip_rate_limit(eip['op_floatingip_id'],
                                                   rate_limit=bandwidth)
        except Exception as e:
            exceptions.append({
                'eip': None,
                'exception': e
            })
        else:
            Eip.update(eip_id, **{
                'bandwidth': bandwidth,
                'updated': datetime.datetime.utcnow(),
            })
            updateds.append(eip_id)

    logger.info('.update() OK, updateds: %s, exceptions: %s' %
                (len(updateds), len(exceptions)))

    return model.actions_result(updateds,
                                exceptions)


def _pre_associate(project_id, eip_id, instance_id):
    """
    eip should be active, instance should not be associated before
    """
    from icebox.model.iaas import network as network_model

    with base.lock_for_update():
        eip = get(eip_id)
        instance = instance_model.get(instance_id)

    eip.must_belongs_project(project_id)
    instance.must_belongs_project(project_id)

    if not eip.status_associable():
        raise iaas_error.EipCanNotAssociate(eip_id)

    if not instance.status_associable():
        raise iaas_error.InstanceCanNotBeAssociated(instance_id)

    # the instance's network should have external_gateway
    network_id = instance['network_id']
    network = network_model.get(network_id)
    if not network['external_gateway_ip']:
        raise iaas_error.AssociateEipWithUnreachableInstance(eip_id, network_id)  # noqa

    try:
        eip_resource_model.get(eip_id)
    except iaas_error.EipResourceNotFound:
        pass
    else:
        # weird, because if eip is not associated,
        # then eip_resource will not exist.
        # this is an internal error.
        raise iaas_error.ServerInternalError('eip %s status not valid.' % eip_id)  # noqa

    return eip, instance, network


@base.transaction
def associate(project_id, eip_id, instance_id):
    """
    acquire eip lock
    acquire instance lock
    """
    eip, instance, network = _pre_associate(project_id, eip_id, instance_id)

    logger.info('.associate() begin, associate eip:%s and instance: %s' %
                (eip_id, instance_id))

    try:
        op_api.do_update_floatingip_port(eip['op_floatingip_id'],
                                         instance['op_port_id'])
    except:
        # should wrap it to icebox error?
        # TODO
        raise

    else:
        Eip.update(eip_id, **{
            'status': EIP_STATUS_ASSOCIATED,
            'updated': datetime.datetime.utcnow(),
        })
        eip_resource_model.create(eip_id=eip_id,
                                  resource_id=instance_id,
                                  resource_type=RESOURCE_TYPE_INSTANCE)

    logger.info('.associate() OK.')
    return eip_id


def _pre_dissociate(project_id, eip_ids):
    eips = []
    for eip_id in eip_ids:
        with base.lock_for_update():
            eip = get(eip_id)

        eip.must_belongs_project(project_id)
        if not eip.status_dissociable():
            raise iaas_error.EipCanNotDissociate(eip_id)

        try:
            eip_resource = eip_resource_model.get(eip_id)
        except iaas_error.EipResourceNotFound:
            # that's weird, because if eip status is 'associated',
            # there must be a eip_resource record.
            # this is an internal error.
            raise iaas_error.ServerInternalError('eip %s status not valid.' % eip_id)  # noqa
        else:
            if (eip_resource['resource_type'] == RESOURCE_TYPE_INSTANCE):
                instance_id = eip_resource['resource_id']
                with base.lock_for_update():
                    instance = instance_model.get(instance_id)

                if not instance.status_dissociable():
                    raise iaas_error.InstanceCanNotBeDissociated(instance_id)

        eips.append(eip)

    return eips


@base.transaction
def dissociate(project_id, eip_ids):
    """
    acquire eip lock
    acquire instance lock if resource_type is instance
    """
    eips = _pre_dissociate(project_id, eip_ids)

    logger.info('.dissociate() begin, total count: %s, eip_ids: %s' %
                (len(eip_ids), eip_ids))

    dissociates = []
    exceptions = []
    for eip in eips:
        try:
            op_api.do_update_floatingip_port(eip['op_floatingip_id'],
                                             op_port_id=None)
        except Exception as e:
            exceptions.append({
                'eip': eip['id'],
                'exception': e
            })
        else:
            Eip.update(eip['id'], **{
                'status': EIP_STATUS_ACTIVE,
                'updated': datetime.datetime.utcnow(),
            })
            eip_resource_model.delete(eip['id'])
            dissociates.append(eip['id'])

    logger.info('.dissociate() OK, dissociates: %s, exceptions: %s' %
                (len(dissociates), len(exceptions)))

    return model.actions_result(dissociates,
                                exceptions)


def _pre_delete(project_id, eip_ids):
    eips = []

    for eip_id in eip_ids:
        with base.lock_for_update():
            eip = get(eip_id)

        eip.must_belongs_project(project_id)
        if not eip.status_deletable():
            raise iaas_error.EipCanNotDelete(eip_id)

        eips.append(eip)

    return eips


@base.transaction
def delete(project_id, eip_ids):
    """
    acquire project lock
    acquire eip lock
    """
    logger.info('.delete() begin, total count: %s, eip_ids: %s' %
                (len(eip_ids), eip_ids))

    with base.lock_for_update():
        project = project_model.get(project_id)

    eips = _pre_delete(project_id, eip_ids)
    addresses = [eip['address'] for eip in eips]

    for eip_id in eip_ids:
        Eip.update(eip_id, **{
            'status': EIP_STATUS_DELETED,
            'deleted': datetime.datetime.utcnow(),
        })

    project.release_quota('eips', len(eip_ids))
    floatingip_model.release_ips(addresses)

    logger.info('.delete() OK: %s')

    job_model.create(
        action='EraseEips',
        params={
            'resource_ids': eip_ids
        },
        run_at=utils.seconds_later(10),   # as fast as possible
        try_period=10)


def modify(project_id, eip_id, name=None, description=None):
    logger.info('.modify() begin, eip: %s' % eip_id)

    eip = get(eip_id)
    eip.must_belongs_project(project_id)

    if name is None:
        name = eip['name']

    if description is None:
        description = eip['description']

    Eip.update(eip_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')

    eip = get(eip_id)
    return eip


def get(eip_id):
    logger.info('.get() begin, eip: %s' % eip_id)

    eip = Eip.get_as_model(eip_id)
    if eip is None:
        raise iaas_error.EipNotFound(eip_id)

    resource_rels = eip_resource_model.relations_from_eips([eip_id])
    eip['resource_type'] = resource_rels[eip_id][0]
    eip['resource_id'] = resource_rels[eip_id][1]

    logger.info('.get() OK.')
    return eip


def get_resource(resource_type, resource_id):
    logger.info('.get_resource() begin, resource_type: %s, resource_id: %s' %
                (resource_type, resource_id))
    if resource_type is None or resource_id is None:
        return None

    try:
        if resource_type == RESOURCE_TYPE_INSTANCE:
            logger.info('resource type is instance.')
            instance = instance_model.get(resource_id)
            logger.info('.get_resource() OK.')
            return instance
    except Exception:
        stack = traceback.format_exc()
        logger.error(stack)
        logger.error('eip_resource data inconsistency! maybe eip is associated with a none exists resource ?!')  # noqa
        return None

    return None


def limitation(status=None, project_ids=None, eip_ids=None, addresses=None,
               op_floatingip_ids=None, verbose=False,
               search_word=None, offset=0, limit=10, reverse=True):
    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, eip_ids)
        _where = filters.filter_addresses(_where, t, addresses)
        _where = filters.filter_op_floatingip_ids(_where, t, op_floatingip_ids)
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filters.filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() begin')
    page = Eip.limitation_as_model(where,
                                   limit=limit,
                                   offset=offset,
                                   order_by=filters.order_by(reverse))

    eip_ids = [eip['id'] for eip in page['items']]
    logger.info('get %s eips from Eip.limitation_as_model.' % len(eip_ids))

    resource_rels = eip_resource_model.relations_from_eips(eip_ids)

    for eip in page['items']:
        resource_type, resource_id = resource_rels[eip['id']]
        eip['resource_type'] = resource_type
        eip['resource_id'] = resource_id

        if verbose:
            logger.debug('require verbose result. start get_resource for eip: %s' % eip['id'])  # noqa
            eip['resource'] = get_resource(resource_type, resource_id)

    logger.info('.limitation() OK.')
    return page


def erase(eip_id):
    logger.info('.erase() begin, eip: %s' % eip_id)
    eip = get(eip_id)

    if eip['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if eip['status'] == EIP_STATUS_DELETED:
        op_api.do_delete_floatingip(eip['op_floatingip_id'])

        Eip.update(eip_id, **{
            'ceased': datetime.datetime.utcnow(),
        })
        logger.info('.erase() OK. ceased.')

    else:
        logger.warn('eip status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
