from icebox import model
import datetime
import traceback
import urlparse

from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from densefog.model.job import job as job_model

from icebox import config
from icebox.model.project import project as project_model
from icebox.model.iaas import instance_type as instance_type_model
from icebox.model.iaas import image as image_model
from icebox.model.iaas import eip_resource as eip_resource_model
from icebox.model.iaas import subnet as subnet_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import key_pair as key_pair_model
from icebox.model.iaas import instance_volume as instance_volume_model
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas import waiter

from icebox.model.iaas.openstack import compute as compute_provider
from icebox.model.iaas.openstack import api as op_api

from densefog import logger
logger = logger.getChild(__file__)

WAIT_BOOT_VOLUME_TIMEOUT = 120
WAIT_DATA_VOLUME_TIMEOUT = 60
WAIT_PORT_TIMEOUT = 60
WAIT_DELETE_SERVER_TIMEOUT = 600
WAIT_CREATE_SERVER_TIMEOUT = 600

INSTANCE_STATUS_PENDING = 'pending'
INSTANCE_STATUS_ACTIVE = 'active'
INSTANCE_STATUS_STARTING = 'starting'
INSTANCE_STATUS_STOPPED = 'stopped'
INSTANCE_STATUS_STOPPING = 'stopping'
INSTANCE_STATUS_RESTARTING = 'restarting'
INSTANCE_STATUS_SCHEDULING = 'scheduling'
INSTANCE_STATUS_DELETED = 'deleted'
INSTANCE_STATUS_CEASED = 'ceased'
INSTANCE_STATUS_ERROR = 'error'

POWER_STATE_MAP = {
    compute_provider.SERVER_POWER_STATE_NO_STATE: INSTANCE_STATUS_PENDING,  # noqa
    compute_provider.SERVER_POWER_STATE_RUNNING: INSTANCE_STATUS_ACTIVE,
    compute_provider.SERVER_POWER_STATE_BLOCKED: INSTANCE_STATUS_STOPPED,
    compute_provider.SERVER_POWER_STATE_PAUSED: INSTANCE_STATUS_STOPPED,
    compute_provider.SERVER_POWER_STATE_SHUTDOWN: INSTANCE_STATUS_STOPPED,
    compute_provider.SERVER_POWER_STATE_SHUTOFF: INSTANCE_STATUS_STOPPED,
    compute_provider.SERVER_POWER_STATE_CRASHED: INSTANCE_STATUS_STOPPED,
    compute_provider.SERVER_POWER_STATE_SUSPENDED: INSTANCE_STATUS_STOPPED,
    compute_provider.SERVER_POWER_STATE_FAILED: INSTANCE_STATUS_STOPPED,
    compute_provider.SERVER_POWER_STATE_BUILDING: INSTANCE_STATUS_PENDING,
}

TASK_STATE_MAP = {
    compute_provider.SERVER_TASK_STATE_SCHEDULING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_BLOCK_DEVICE_MAPPING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_NETWORKING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_SPAWNING: INSTANCE_STATUS_PENDING,
    compute_provider.SERVER_TASK_STATE_IMAGE_SNAPSHOT: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_IMAGE_SNAPSHOT_PENDING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_IMAGE_PENDING_UPLOAD: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_IMAGE_UPLOADING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_IMAGE_BACKUP: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_UPDATING_PASSWORD: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_RESIZE_PREP: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_RESIZE_MIGRATING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_RESIZE_MIGRATED: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_RESIZE_FINISH: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_RESIZE_REVERTING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_RESIZE_CONFIRMING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_REBOOTING: INSTANCE_STATUS_RESTARTING,
    compute_provider.SERVER_TASK_STATE_REBOOT_PENDING: INSTANCE_STATUS_RESTARTING,  # noqa
    compute_provider.SERVER_TASK_STATE_REBOOT_STARTED: INSTANCE_STATUS_RESTARTING,  # noqa
    compute_provider.SERVER_TASK_STATE_REBOOTING_HARD: INSTANCE_STATUS_RESTARTING,  # noqa
    compute_provider.SERVER_TASK_STATE_REBOOT_PENDING_HARD: INSTANCE_STATUS_RESTARTING,  # noqa
    compute_provider.SERVER_TASK_STATE_REBOOT_STARTED_HARD: INSTANCE_STATUS_RESTARTING,  # noqa
    compute_provider.SERVER_TASK_STATE_PAUSING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_UNPAUSING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_SUSPENDING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_RESUMING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_POWERING_OFF: INSTANCE_STATUS_STOPPING,  # noqa
    compute_provider.SERVER_TASK_STATE_POWERING_ON: INSTANCE_STATUS_STARTING,
    compute_provider.SERVER_TASK_STATE_RESCUING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_UNRESCUING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_REBUILDING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_REBUILD_BLOCK_DEVICE_MAPPING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_REBUILD_SPAWNING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_MIGRATING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_DELETING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_SOFT_DELETING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_RESTORING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_SHELVING: INSTANCE_STATUS_SCHEDULING,
    compute_provider.SERVER_TASK_STATE_SHELVING_IMAGE_PENDING_UPLOAD: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_SHELVING_IMAGE_UPLOADING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_SHELVING_OFFLOADING: INSTANCE_STATUS_SCHEDULING,  # noqa
    compute_provider.SERVER_TASK_STATE_UNSHELVING: INSTANCE_STATUS_SCHEDULING,
}

RESTART_TYPE_SOFT = 'SOFT'
RESTART_TYPE_HARD = 'HARD'


class Instance(base.ResourceModel):

    @classmethod
    def db(cls):
        return db.DB.instance

    def status_startable(self):
        return self['status'] in [
            INSTANCE_STATUS_STOPPED
        ]

    def status_stopable(self):
        return self['status'] in [
            INSTANCE_STATUS_ACTIVE,
            INSTANCE_STATUS_ERROR
        ]

    def status_deletable(self):
        return self['status'] in [
            INSTANCE_STATUS_ACTIVE,
            INSTANCE_STATUS_STOPPED,
            INSTANCE_STATUS_ERROR
        ]

    def status_attachable(self):
        return self['status'] in [
            INSTANCE_STATUS_ACTIVE,
            INSTANCE_STATUS_STOPPED
        ]

    def status_detachable(self):
        return self['status'] in [
            INSTANCE_STATUS_ACTIVE,
            INSTANCE_STATUS_STOPPED
        ]

    def status_associable(self):
        return self['status'] in [
            INSTANCE_STATUS_ACTIVE,
            INSTANCE_STATUS_STOPPED
        ]

    def status_dissociable(self):
        return self['status'] in [
            INSTANCE_STATUS_ACTIVE,
            INSTANCE_STATUS_STOPPED
        ]

    def status_restartable(self):
        return self['status'] in [
            INSTANCE_STATUS_ACTIVE
        ]

    def status_resizable(self):
        return self['status'] in [
            INSTANCE_STATUS_STOPPED
        ]

    def status_resetable(self):
        return self['status'] in [
            INSTANCE_STATUS_STOPPED
        ]

    def status_login_changable(self):
        return self['status'] in [
            INSTANCE_STATUS_ACTIVE
        ]

    def boot_from_volume(self):
        return bool(self['op_volume_id'])

    def format(self):
        formated = {
            'instanceId': self['id'],
            'projectId': self['project_id'],
            'name': self['name'],
            'description': self['description'],
            'instanceTypeId': self['instance_type_id'],
            'imageId': self['image_id'],
            'currentVCPUs': self['current_vcpus'],
            'currentMemory': self['current_memory'],
            'currentDisk': self['current_disk'],
            'address': self['address'],
            'networkId': self['network_id'],
            'subnetId': self['subnet_id'],
            'keyPairId': self['key_pair_id'],
            'status': self['status'],
            'created': self['created'],
            'updated': self['updated'],
            'deleted': self['deleted'],
            'ceased': self['ceased'],
        }
        try:
            formated['eipId'] = self['eip_id']
        except:
            formated['eipId'] = None

        try:
            formated['volumeIds'] = self['volume_ids']
        except:
            formated['volumeIds'] = None

        return formated


def _validate_login_mode(login_mode, key_pair_id, login_password):
    logger.debug('check input password and key_pair...')

    if login_mode == 'password':
        key_pair_id = None
        if login_password is None:
            raise iaas_error.InstanceLoginModeError()

        if not utils.strong_password(login_password):
            raise iaas_error.InstanceLoginPasswordWeak()

    elif login_mode == 'keyPair':
        login_password = None
        if key_pair_id is None:
            raise iaas_error.InstanceLoginModeError()

        # fetch it. prove it exists
        with base.lock_for_update():
            key_pair = key_pair_model.get(key_pair_id)

        key_pair.must_be_available()

    else:
        raise iaas_error.InstanceLoginModeError()

    logger.debug('check input ok.')

    return key_pair_id, login_password


def _validate_instance_name(name):
    """
    instance name should be very simple. do not complex.
    for now. these characters:  a-z A-Z  0-9  -  _
    None or empty, is considered quite simple. :)
    """
    if not utils.simple_name(name):
        raise iaas_error.InstanceNameTooComplex()

    return name


def _pre_create(project, image_id, instance_type_id, subnet_id, ip_address,
                count):
    """
    Preconditions

    The user must have sufficient server quota to
        create the number of servers requested.
    The connection to the Image service is valid.
    """

    # do not lock image or instance_type,
    # they are likely to be public, others may use it to create instance
    image = image_model.get(image_id)
    instance_type = instance_type_model.get(instance_type_id)
    # lock subnet and network.
    with base.lock_for_update():
        subnet = subnet_model.get(subnet_id)
        network = network_model.get(subnet['network_id'])

    image.must_be_available()
    instance_type.must_be_available()
    subnet.must_be_available()
    network.must_be_available()

    # if user supply ip, then this ip must be in subnet and count should be 1.
    if ip_address:
        if not subnet.contain_address(ip_address) or count > 1:
            raise iaas_error.CreateInstanceWhenIpAddressNotValid(ip_address)

    if (instance_type['disk'] < image['min_disk'] or
       instance_type['vcpus'] < image['min_vcpus'] or
       instance_type['memory'] < image['min_memory']):

        raise iaas_error.CreateInstanceWhenFlavorTooSmall(instance_type['id'],
                                                          image['id'])

    logger.debug('check if project has enough quota...')

    project.must_have_enough_quotas(instances=count,
                                    vcpus=count * instance_type['vcpus'],
                                    memory=count * instance_type['memory'])

    logger.debug('check quota ok.')

    return image, instance_type, network, subnet


@utils.footprint(logger)
def create(project_id, name,
           image_id, instance_type_id,
           login_mode, key_pair_id, login_password, subnet_id, ip_address=None,
           user_data=None, count=1):
    """
    acquire project lock
    acquire subnet lock
    acquire network lock
    acquire key_pair lock, if login_mode is key_pair
    """
    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        image, instance_type, network, subnet = _pre_create(project,
                                                            image_id,
                                                            instance_type_id,
                                                            subnet_id,
                                                            ip_address,
                                                            count)
        vcpus = instance_type['vcpus']
        memory = instance_type['memory']
        disk = instance_type['disk']

        key_pair_id, login_password = _validate_login_mode(login_mode,
                                                           key_pair_id,
                                                           login_password)

        _validate_instance_name(name)

        # assume creations all success.
        project.consume_quotas(instances=count,
                               vcpus=count * vcpus,
                               memory=count * memory)

    creatings = []
    creating_jobs = []
    for i in range(count):
        instance_id = 'i-%s' % utils.generate_key(8)

        dm_op_volume_id = 'dummy-' + utils.generate_key(30)        # 36 chars
        dm_op_server_id = 'dummy-' + utils.generate_key(30)        # 36 chars
        dm_op_port_id = 'dummy-' + utils.generate_key(30)          # 36 chars
        dm_address = ''

        instance_id = Instance.insert(**{
            'id': instance_id,
            'project_id': project_id,
            'name': name,
            'description': '',
            'instance_type_id': instance_type_id,
            'image_id': image['id'],
            'op_volume_id': dm_op_volume_id,                        # dummy
            'current_vcpus': vcpus,
            'current_memory': memory,
            'current_disk': disk,
            'op_server_id': dm_op_server_id,                        # dummy
            'address': dm_address,                                  # dummy
            'op_network_id': network['op_network_id'],
            'op_subnet_id': subnet['op_subnet_id'],
            'op_port_id': dm_op_port_id,                            # dummy
            'network_id': network['id'],
            'subnet_id': subnet['id'],
            'key_pair_id': None,                                    # dummy
            'status': INSTANCE_STATUS_PENDING,
            'updated': datetime.datetime.utcnow(),
            'created': datetime.datetime.utcnow(),
        })

        # it takes long time, so schedule a job.
        job_id = job_model.create(
            action='CreateServer',
            project_id=project_id,
            try_period=config.CONF.try_period,
            params={
                'args': {
                    'instance_id': instance_id,
                    'key_pair_id': key_pair_id,
                    'login_password': login_password,
                    'ip_address': ip_address,
                    'user_data': user_data,
                },
                'resource_ids': [instance_id]  # for response.
            }
        )

        creatings.append(instance_id)
        creating_jobs.append(job_id)

    logger.info('creatings: %s' % len(creatings))

    # this job is watching other rebuilding jobs.
    job_id = job_model.create(
        action='WatchingJobs',
        project_id=project_id,
        try_max=1,  # this job is only need to run once, doesn't need retry
        run_at=utils.seconds_later(2),   # wait 2 seconds.
        try_period=config.CONF.try_period,
        params={
            'job_ids': creating_jobs,
            'resource_ids': creatings
        }
    )
    return job_id


@utils.footprint(logger)
def create_server(instance_id, key_pair_id, login_password, ip_address,
                  user_data):
    """Create server for instance

    step 1: create boot volume
    step 2: create port
    step 3: create server
    step 4: update instance status to active.
    """
    instance = get(instance_id)

    project = project_model.get(instance['project_id'])
    image = image_model.get(instance['image_id'])
    network = network_model.get(instance['network_id'])
    subnet = subnet_model.get(instance['subnet_id'])
    instance_type = instance_type_model.get(instance['instance_type_id'])

    try:
        op_volume = op_api.do_create_boot_volume(project['op_project_id'],
                                                 image['op_image_id'],
                                                 size=instance_type['disk'])
        waiter.wait_volume_available(op_volume['id'], WAIT_BOOT_VOLUME_TIMEOUT)
        instance['op_volume_id'] = op_volume['id']

        port = op_api.do_create_port(project['op_project_id'],
                                     network['op_network_id'],
                                     subnet['op_subnet_id'],
                                     ip_address)
        waiter.wait_port_available(port['id'], timeout=WAIT_PORT_TIMEOUT)

        instance['op_port_id'] = port['id']
        instance['address'] = port['fixed_ips'][0]['ip_address']

        server = op_api.do_create_server(project['op_project_id'],
                                         instance['name'],
                                         op_volume['id'],
                                         instance_type['op_flavor_id'],
                                         port['network_id'],
                                         port['id'],
                                         key_pair_id,
                                         login_password,
                                         user_data)
        # wait for create_server as long as possible.
        waiter.wait_server_available(server['id'],
                                     timeout=WAIT_CREATE_SERVER_TIMEOUT)

        instance['op_server_id'] = server['id']
        instance['key_pair_id'] = key_pair_id

    except Exception:
        # after silently clean up, re-raise current exception
        with utils.defer_reraise():
            with utils.silent():
                op_api.do_delete_server(op_server_id=server['id'])
                waiter.wait_server_deleted(server['id'],
                                           timeout=WAIT_DELETE_SERVER_TIMEOUT)

            # NOTE: still, we have no garauntee that the following boot volumes
            #       can be deleted properly, because they may be in creating
            #       for a long time! which will leave many orphan volumes
            with utils.silent():
                op_api.do_delete_volume(op_volume_id=op_volume['id'])

            with utils.silent():
                op_api.do_delete_port(op_port_id=port['id'])

    # save them to db.
    Instance.update(instance_id, **{
        'op_volume_id': instance['op_volume_id'],
        'op_server_id': instance['op_server_id'],
        'address': instance['address'],
        'op_port_id': instance['op_port_id'],
        'key_pair_id': instance['key_pair_id'],
        'status': INSTANCE_STATUS_ACTIVE,
        'updated': datetime.datetime.utcnow(),
    })

    return get(instance_id)


@utils.footprint(logger)
def create_server_failed(instance_id):
    """Create server process is failed. mark instance error
    """
    Instance.update(instance_id, **{
        'status': INSTANCE_STATUS_ERROR,
        'updated': datetime.datetime.utcnow(),
    })


def _pre_delete(project_id, instance_ids):
    """
    Preconditions

    The server must exist.
    must not have volumes attaching
    must not have eip associating.
    """

    instances = []
    for instance_id in instance_ids:
        with base.lock_for_update():
            instance = get(instance_id)

        instance.must_belongs_project(project_id)
        instance.must_not_busy()

        if not instance.status_deletable():
            raise iaas_error.InstanceCanNotDelete(instance_id)

        if instance['volume_ids']:
            raise iaas_error.DeleteInstanceWhenVolumesAttaching(instance_id,
                                                                instance['volume_ids'])   # noqa

        if instance['eip_id']:
            raise iaas_error.DeleteInstanceWhenEipAssociating(instance_id,
                                                              instance['eip_id'])   # noqa

        instances.append(instance)

    return instances


@utils.footprint(logger)
def delete(project_id, instance_ids):
    """
    delete instances.
    """
    logger.info('total count: %s, instance_ids: %s' %
                (len(instance_ids), instance_ids))

    qt_instances = 0
    qt_vcpus = 0
    qt_memory = 0

    exceptions = []
    deleteds = []

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            instances = _pre_delete(project_id, instance_ids)

            for instance in instances:
                # delete subnet port for this server at first.
                # because user may delete subnet immediately, but at that time
                # the async job EraseInstances have not been executed. and
                # delete subnet will fail.
                with utils.silent(lambda ex: logger.trace(ex)):
                    op_api.do_interface_detach(instance)

                try:
                    op_api.do_delete_port(instance=instance)
                except Exception as ex:
                    exceptions.append({
                        'instance': instance['id'],
                        'exception': ex
                    })
                    # it's a exception. and we go to next loop.
                    continue

                # stop the server,
                # after delete instances, actually erase will be 2 hours later.
                # we donot want the resources showing active in openstack.
                # if we cannot stop the server(maybe in error state ?)
                # just ignore it. job worker do delete,
                # if job still cannot delete, worker will complain,
                with utils.silent(lambda ex: logger.trace(ex)):
                    op_api.do_stop_server(instance)

                qt_instances += 1
                qt_vcpus += instance['current_vcpus']
                qt_memory += instance['current_memory']

                deleteds.append(instance['id'])

                Instance.update(instance['id'], **{
                    'status': INSTANCE_STATUS_DELETED,
                    'deleted': datetime.datetime.utcnow(),
                })

    # releaes those quotas at very late time.
    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)
            project.release_quotas(instances=qt_instances,
                                   vcpus=qt_vcpus,
                                   memory=qt_memory)

    job_model.create(
        action='EraseInstances',
        params={
            'resource_ids': instance_ids
        },
        run_at=utils.seconds_later(config.CONF.erase_delay),
        try_period=config.CONF.try_period)

    return model.actions_result(deleteds,
                                exceptions)


def _pre_start(project_id, instance_ids):
    """
    Preconditions

    The server status must be STOPPED.
    If the server is locked,
        you must have administrator privileges to start the server.
    """
    instances = []
    for instance_id in instance_ids:
        with base.lock_for_update():
            instance = get(instance_id)

        instance.must_belongs_project(project_id)
        instance.must_not_busy()

        if not instance.status_startable():
            raise iaas_error.InstanceCanNotStart(instance_id)

        instances.append(instance)
    return instances


@utils.footprint(logger)
def start(project_id, instance_ids):
    """
    start instances
    """
    logger.info('total count: %s, instance_ids: %s' %
                (len(instance_ids), instance_ids))

    startings = []
    exceptions = []

    with base.open_transaction(db.DB):
        instances = _pre_start(project_id, instance_ids)
        for instance in instances:
            try:
                op_api.do_start_server(instance)
            except Exception as ex:
                exceptions.append({
                    'instance': instance['id'],
                    'exception': ex
                })
                continue

            Instance.update(instance['id'], **{
                'status': INSTANCE_STATUS_STARTING,
                'updated': datetime.datetime.utcnow(),
            })
            startings.append(instance['id'])

    logger.info('startings: %s, exceptions: %s' %
                (len(startings), len(exceptions)))

    return model.actions_job('StartInstances',
                             project_id,
                             startings,
                             exceptions)


def _pre_stop(project_id, instance_ids):
    """
    Preconditions

    The server status must be ACTIVE or ERROR.
    """
    instances = []
    for instance_id in instance_ids:
        with base.lock_for_update():
            instance = get(instance_id)

        instance.must_belongs_project(project_id)
        instance.must_not_busy()

        if not instance.status_stopable():
            raise iaas_error.InstanceCanNotStop(instance_id)

        instances.append(instance)
    return instances


@utils.footprint(logger)
def stop(project_id, instance_ids):
    """
    stop instances
    """
    logger.info('total count: %s, instance_ids: %s' %
                (len(instance_ids), instance_ids))
    stoppings = []
    exceptions = []

    with base.open_transaction(db.DB):
        instances = _pre_stop(project_id, instance_ids)
        for instance in instances:
            try:
                op_api.do_stop_server(instance)
            except Exception as ex:
                exceptions.append({
                    'instance': instance['id'],
                    'exception': ex
                })
                continue

            Instance.update(instance['id'], **{
                'status': INSTANCE_STATUS_STOPPING,
                'updated': datetime.datetime.utcnow(),
            })
            stoppings.append(instance['id'])

    logger.info('stoppings: %s, exceptions: %s' %
                (len(stoppings), len(exceptions)))

    return model.actions_job('StopInstances',
                             project_id,
                             stoppings,
                             exceptions)


def _pre_restart(project_id, instance_ids):
    """
    instance should be active to restart
    """
    instances = []
    for instance_id in instance_ids:
        with base.lock_for_update():
            instance = get(instance_id)

        instance.must_belongs_project(project_id)
        instance.must_not_busy()

        if not instance.status_restartable():
            raise iaas_error.InstanceCanNotRestart(instance_id)
        instances.append(instance)

    return instances


@utils.footprint(logger)
def restart(project_id, instance_ids, restart_type=RESTART_TYPE_SOFT):
    """
    restart instances.
    """
    logger.info('total count: %s, instance_ids: %s' %
                (len(instance_ids), instance_ids))

    if restart_type:
        restart_type = restart_type.upper()

    restartings = []
    exceptions = []

    with base.open_transaction(db.DB):
        instances = _pre_restart(project_id, instance_ids)
        for instance in instances:
            try:
                op_api.do_reboot_server(instance, restart_type)
            except Exception as ex:
                exceptions.append({
                    'instance': instance['id'],
                    'exception': ex
                })
                continue

            Instance.update(instance['id'], **{
                'status': INSTANCE_STATUS_RESTARTING,
                'updated': datetime.datetime.utcnow(),
            })
            restartings.append(instance['id'])

    logger.info('restartings: %s, exceptions: %s' %
                (len(restartings), len(exceptions)))

    return model.actions_job('RestartInstances',
                             project_id,
                             restartings,
                             exceptions)


def _pre_reset(project_id, instance_ids, image_id):
    instances = []
    for instance_id in instance_ids:
        with base.lock_for_update():
            instance = get(instance_id)

        instance.must_belongs_project(project_id)
        instance.must_not_busy()

        if not instance.status_resetable():
            raise iaas_error.InstanceCanNotReset(instance_id)
        if not instance.boot_from_volume():
            raise iaas_error.InstanceResetUnsupported(instance_id)

        instances.append(instance)

    images = []
    if image_id is not None:
        image = image_model.get(image_id)
        images = [image] * len(instances)
    else:
        for instance in instances:
            try:
                image = image_model.get(instance['image_id'])
                image.must_be_available()
            except Exception:
                raise iaas_error.ResetInstanceWithIllegalImage(instance['id'],
                                                               instance['image_id'])   # noqa
            images.append(image)

    return instances, images


@utils.footprint(logger)
def rebuild_server(instance_id, image_id, key_pair_id, login_password):
    """Rebuild new instances, which are boot from volumes.

    step 1: clean old server and boot_volume
    step 2: create another boot volume from image
    step 3: create server, use the new boot_volume, use old port
    step 4: attach those data volumes.
    """
    instance = get(instance_id)
    image = image_model.get(image_id)

    project = project_model.get(instance['project_id'])
    instance_type = instance_type_model.get(instance['instance_type_id'])

    # clean old server and boot_volume
    with utils.silent():
        op_api.do_delete_server(instance)
        waiter.wait_server_deleted(instance['op_server_id'],
                                   timeout=WAIT_DELETE_SERVER_TIMEOUT)

    with utils.silent():
        op_api.do_delete_boot_volume(instance)

    try:
        # create another boot volume
        op_volume = op_api.do_create_boot_volume(project['op_project_id'],
                                                 image['op_image_id'],
                                                 size=instance_type['disk'])
        op_volume_id = op_volume['id']             # new boot volume
        op_port_id = instance['op_port_id']        # old port

        # make sure new boot volume and port are available.
        waiter.wait_volume_available(op_volume_id, WAIT_BOOT_VOLUME_TIMEOUT)
        instance['op_volume_id'] = op_volume_id

        waiter.wait_port_available(op_port_id, WAIT_PORT_TIMEOUT)

        server = op_api.do_create_server(project['op_project_id'],
                                         instance['name'],
                                         op_volume_id,
                                         instance_type['op_flavor_id'],
                                         instance['op_network_id'],
                                         op_port_id,
                                         key_pair_id,
                                         login_password,
                                         None)
        instance['op_server_id'] = server['id']

        # wait for create_server as long as possible.
        # only if server is available, can volumes be attached to it.
        waiter.wait_server_available(server['id'],
                                     timeout=WAIT_CREATE_SERVER_TIMEOUT)

    except Exception:
        # after silently clean up, re-raise current exception
        with utils.defer_reraise():

            with utils.silent():
                op_api.do_delete_server(op_server_id=server['id'])
                waiter.wait_server_deleted(server['id'],
                                           timeout=WAIT_DELETE_SERVER_TIMEOUT)  # noqa

            with utils.silent():
                op_api.do_delete_boot_volume(op_volume_id=op_volume['id'])

    # get those attached data volumes.
    attacheds, detacheds = _attach_data_volumes(instance)

    # server is ready. save it to db.
    Instance.update(instance['id'], **{
        'op_volume_id': instance['op_volume_id'],
        'op_server_id': instance['op_server_id'],
        'status': INSTANCE_STATUS_ACTIVE,
        'updated': datetime.datetime.utcnow(),
    })

    return server


def rebuild_server_failed(instance_id):
    """ Rebuild process is failed. mark instance error
    """
    Instance.update(instance_id, **{
        'status': INSTANCE_STATUS_ERROR,
        'updated': datetime.datetime.utcnow(),
    })


@utils.footprint(logger)
def _attach_data_volumes(instance):
    """Attach data volumes to the instance

    some volume may failed to attach, return those attacheds and detacheds.
    """
    from icebox.model.iaas import volume as volume_model

    volumes = []
    try:
        for volume_id in instance['volume_ids']:
            volume = volume_model.get(volume_id)
            waiter.wait_volume_available(volume['op_volume_id'],
                                         timeout=WAIT_DATA_VOLUME_TIMEOUT)
            volumes.append(volume)
    except Exception:
        raise

    # if some data volumes attach FAILED, we should know that, and
    # report administrator
    detacheds = []
    attacheds = []
    for volume in volumes:
        try:
            op_api.do_attach_volume(instance, volume)
            # wait attaching success before attach next volume.
            waiter.wait_volume_inuse(volume['op_volume_id'],
                                     timeout=WAIT_DATA_VOLUME_TIMEOUT)
            attacheds.append(volume['id'])

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)

            # attach fail. mark available in icebox db.
            instance_volume_model.delete(volume_id=volume['id'])
            volume_model.Volume.update(volume['id'], **{
                'status': volume_model.VOLUME_STATUS_ACTIVE,
                'updated': datetime.datetime.utcnow(),
            })
            detacheds.append(volume['id'])

    logger.info('attached %d volumes. %d volumes not attached back.' % (
                len(attacheds), len(detacheds)))
    if detacheds:
        # TODO. how do we notify user, that some of the volumes
        # are not attached back????
        logger.error('volumes[%s] are not attached back!' % detacheds)
        pass

    return (attacheds, detacheds)


@utils.footprint(logger)
def reset(project_id, instance_ids, login_mode, key_pair_id, login_password,
          image_id=None):
    """
    reset instances. use image_id. if image_id is None,
    then use instance's original image
    """
    logger.info('total count: %s, instance_ids: %s' %
                (len(instance_ids), instance_ids))
    with base.open_transaction(db.DB):
        instances, images = _pre_reset(project_id, instance_ids, image_id)
        key_pair_id, login_password = _validate_login_mode(login_mode,
                                                           key_pair_id,
                                                           login_password)
        resetings = []
        reseting_jobs = []

        for index, instance in enumerate(instances):
            image = images[index]
            # it takes long time, so schedule a job.
            job_id = job_model.create(
                action='RebuildServer',
                project_id=project_id,
                try_period=config.CONF.try_period,
                params={
                    'args': {
                        'instance_id': instance['id'],
                        'image_id': image['id'],
                        'key_pair_id': key_pair_id,
                        'login_password': login_password,
                    },
                    'resource_ids': [instance['id']]  # for response.
                }
            )
            reseting_jobs.append(job_id)

            Instance.update(instance['id'], **{
                'key_pair_id': key_pair_id,
                'image_id': image['id'],
                'status': INSTANCE_STATUS_SCHEDULING,
                'updated': datetime.datetime.utcnow(),
            })
            resetings.append(instance['id'])

    logger.info('resetings: %s' % len(resetings))

    # this job is watching other rebuilding jobs.
    job_id = job_model.create(
        action='WatchingJobs',
        project_id=project_id,
        try_max=1,  # this job is only need to run once, doesn't need retry
        run_at=utils.seconds_later(2),   # wait 2 seconds.
        try_period=config.CONF.try_period,
        params={
            'job_ids': reseting_jobs
        }
    )
    return job_id


def _pre_resize(project, instance_ids, instance_type_id):
    """
    Preconditions

    You can only resize a server when its status is ACTIVE or STOPPED.
    """
    delta_vcpus = 0
    delta_memory = 0

    instance_type = instance_type_model.get(instance_type_id)

    instances = []
    for instance_id in instance_ids:
        with base.lock_for_update():
            instance = get(instance_id)

        if not instance.status_resizable():
            raise iaas_error.InstanceCanNotResize(instance_id)

        if not instance.boot_from_volume():
            raise iaas_error.InstanceResizeUnsupported(instance_id)

        instance.must_belongs_project(project['id'])

        delta_vcpus += instance_type['vcpus'] - instance['current_vcpus']
        delta_memory += instance_type['memory'] - instance['current_memory']

        # we should check in the for in loop. and check one by one.
        project.must_have_enough_quotas(vcpus=delta_vcpus,
                                        memory=delta_memory)

        instances.append(instance)

    return instances, instance_type, delta_vcpus, delta_memory


@utils.footprint(logger)
def resize(project_id, instance_ids, instance_type_id):
    """
    resize instances.
    """
    logger.info('total count: %s, instance_ids: %s' %
                (len(instance_ids), instance_ids))
    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)

        instances, instance_type, delta_vcpus, delta_memory = _pre_resize(
            project, instance_ids, instance_type_id)

        # assume resizings all success.
        project.consume_quotas(vcpus=delta_vcpus,
                               memory=delta_memory)

    qt_vcpus = 0
    qt_memory = 0

    resizings = []
    exceptions = []

    with base.open_transaction(db.DB):
        instances, instance_type, delta_vcpus, delta_memory = _pre_resize(
            project, instance_ids, instance_type_id)

        for instance in instances:
            try:
                op_api.do_resize_server(instance, instance_type)
            except Exception as ex:
                exceptions.append({
                    'instance': instance['id'],
                    'exception': ex
                })
                continue

            qt_vcpus += instance_type['vcpus'] - instance['current_vcpus']
            qt_memory += instance_type['memory'] - instance['current_memory']  # noqa

            Instance.update(instance['id'], **{
                'instance_type_id': instance_type_id,
                'current_vcpus': instance_type['vcpus'],
                'current_memory': instance_type['memory'],
                'current_disk': instance_type['disk'],
                'status': INSTANCE_STATUS_SCHEDULING,
                'updated': datetime.datetime.utcnow(),
            })
            resizings.append(instance['id'])

    with base.open_transaction(db.DB):
        with base.lock_for_update():
            project = project_model.get(project_id)
        # but we actually consume qt_vcpus, release those left.
        project.release_quotas(vcpus=delta_vcpus - qt_vcpus,
                               memory=delta_memory - qt_memory)

    logger.info('resizings: %s, exceptions: %s' %
                (len(resizings), len(exceptions)))

    return model.actions_job('ResizeInstances',
                             project_id,
                             resizings,
                             exceptions)


@base.transaction
@utils.footprint(logger)
def change_password(project_id, instance_id, login_password):
    """
    change root login_password
    """
    if not utils.strong_password(login_password):
        raise iaas_error.InstanceLoginPasswordWeak()

    with base.lock_for_update():
        instance = get(instance_id)
    if not instance.status_login_changable():
        raise iaas_error.InstanceCanNotChangePassword(instance_id)

    try:
        op_api.do_change_password(instance, login_password)
    except:
        # sync instance status.
        job_model.create(
            action='SyncInstances',
            params={
                'resource_ids': [instance_id]
            },
            run_at=utils.seconds_later(10),  # as fast as possible
            try_period=10)

        raise

    Instance.update(instance['id'], **{
        'updated': datetime.datetime.utcnow(),
    })

    return instance_id


@base.transaction
@utils.footprint(logger)
def change_key_pair(project_id, instance_id, key_pair_id):
    """
    change root key_pair_id
    """
    with base.lock_for_update():
        instance = get(instance_id)
    if not instance.status_login_changable():
        raise iaas_error.InstanceCanNotChangeKeyPair(instance_id)

    key_pair = key_pair_model.get(key_pair_id)
    key_pair.must_be_available()

    try:
        op_api.do_change_keypair(instance, key_pair_id)
    except:
        # sync instance status.
        job_model.create(
            action='SyncInstances',
            params={
                'resource_ids': [instance_id]
            },
            run_at=utils.seconds_later(10),  # as fast as possible
            try_period=10)

        raise

    Instance.update(instance['id'], **{
        'key_pair_id': key_pair_id,
        'updated': datetime.datetime.utcnow(),
    })

    return instance_id


@utils.footprint(logger)
def modify(project_id, instance_id, name=None, description=None):
    """
    modify instances. name & description
    """
    logger.info('.modify() begin. instance_id: %s' % instance_id)

    instance = get(instance_id)
    instance.must_belongs_project(project_id)

    if name is None:
        name = instance['name']

    _validate_instance_name(name)

    if description is None:
        description = instance['description']

    Instance.update(instance_id, **{
        'name': name,
        'description': description,
        'updated': datetime.datetime.utcnow(),
    })

    logger.info('.modify() OK.')

    return instance_id


@utils.footprint(logger)
def sync(instance_id):
    logger.info('instance_id: %s' % instance_id)

    instance = get(instance_id)
    server_id = instance['op_server_id']

    try:
        server = op_api.do_get_server(server_id)
    except:
        Instance.update(instance_id, **{
            'status': INSTANCE_STATUS_ERROR,
            'updated': datetime.datetime.utcnow(),
        })
        raise

    if instance.is_deleted():
        logger.info('instance is already deleted, skip it.')
        return instance

    server_status = server['status']
    power_state = server['power_state']
    task_state = server['task_state']
    vm_state = server['vm_state']

    status = INSTANCE_STATUS_PENDING
    if task_state:
        status = TASK_STATE_MAP[task_state]
    else:
        status = POWER_STATE_MAP[power_state]

    if server_status == compute_provider.SERVER_STATUS_VERIFY_RESIZE:
        logger.info('provider confirm_server_resize.'
                    'maybe confirmed before, anyway, try catch.')

        with utils.silent():
            op_api.do_confirm_resize_server(server_id)

        status = INSTANCE_STATUS_SCHEDULING

    if server_status == compute_provider.SERVER_STATUS_ERROR:
        status = INSTANCE_STATUS_ERROR

    logger.info('provider instance server_status (%s), power_state (%s), '
                'task_state (%s), vm_state (%s).' %
                (server_status, power_state, task_state, vm_state))

    logger.info('instance (%s) status: (%s) => (%s) .' %
                (instance['id'], instance['status'], status))

    Instance.update(instance_id, **{
        'status': status,
        'updated': datetime.datetime.utcnow(),
    })

    instance = get(instance_id)
    return instance


@utils.footprint(logger)
def get(instance_id):
    logger.info('instance_id: %s' % instance_id)

    instance = Instance.get_as_model(instance_id)
    if instance is None:
        raise iaas_error.InstanceNotFound(instance_id)

    eip_rels = eip_resource_model.relations_from_instances([instance_id])
    instance['eip_id'] = eip_rels[instance_id]

    volumes_rels = instance_volume_model.relations_from_instances([instance_id])  # noqa
    instance['volume_ids'] = volumes_rels[instance_id]

    return instance


@utils.footprint(logger)
def connect_vnc(project_id, instance_id):
    logger.info('instance_id: %s' % instance_id)

    instance = get(instance_id)
    instance.must_belongs_project(project_id)

    server_id = instance['op_server_id']
    vnc = op_api.do_get_vnc_console(server_id)
    p = urlparse.urlparse(vnc['url'])

    return {
        'host': p.hostname,
        'port': p.port,
        'token': urlparse.parse_qs(p.query)['token'][0],
    }


@utils.footprint(logger)
def get_output(project_id, instance_id):
    logger.info('instance_id: %s' % instance_id)

    instance = get(instance_id)
    instance.must_belongs_project(project_id)

    server_id = instance['op_server_id']
    output = op_api.do_get_console_output(server_id)

    return output


@utils.footprint(logger)
def limitation(project_ids=None, instance_ids=None, names=None,
               op_server_ids=None, network_ids=None,
               image_ids=None, status=None, verbose=False, search_word=None,
               offset=0, limit=10, reverse=True):

    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, instance_ids)
        _where = filters.filter_names(_where, t, names)
        _where = filters.filter_op_server_ids(_where, t, op_server_ids)
        _where = filters.filter_project_ids(_where, t, project_ids)
        _where = filters.filter_network_ids(_where, t, network_ids)
        _where = filters.filter_image_ids(_where, t, image_ids)
        _where = filters.filter_search_word(_where, t, search_word)
        _where = filters.filter_status(_where, t, status)
        return _where

    page = Instance.limitation_as_model(where,
                                        offset=offset,
                                        limit=limit,
                                        order_by=filters.order_by(reverse))

    instance_ids = [instance['id'] for instance in page['items']]

    eip_rels = eip_resource_model.relations_from_instances(instance_ids)
    volumes_rels = instance_volume_model.relations_from_instances(instance_ids)  # noqa

    from icebox.model.iaas import eip as eip_model
    from icebox.model.iaas import volume as volume_model

    for instance in page['items']:
        instance['eip_id'] = eip_rels[instance['id']]
        instance['volume_ids'] = sorted(volumes_rels[instance['id']])

        if verbose:
            logger.debug('require verbose result.')

            instance_type_id = instance['instance_type_id']
            image_id = instance['image_id']
            network_id = instance['network_id']
            subnet_id = instance['subnet_id']
            eip_id = instance['eip_id']
            volume_ids = instance['volume_ids']

            instance_type = instance_type_model.get(instance_type_id)
            image = image_model.get(image_id)
            network = network_model.get(network_id)
            subnet = subnet_model.get(subnet_id)
            if eip_id:
                eip = eip_model.get(eip_id)
            else:
                eip = None

            if volume_ids:
                volumes = volume_model.limitation(volume_ids=volume_ids, limit=0)['items']   # noqa
                volumes = sorted(volumes, key=lambda x: x['id'])
            else:
                volumes = []

            instance['instance_type'] = instance_type
            instance['image'] = image
            instance['network'] = network
            instance['subnet'] = subnet
            instance['eip'] = eip
            instance['volumes'] = volumes

    return page


@utils.footprint(logger)
def erase(instance_id):
    logger.info('instance_id: %s' % instance_id)

    instance = get(instance_id)

    if instance['ceased']:
        logger.info('.erase() pass. already ceased.')
        return

    if instance['status'] == INSTANCE_STATUS_DELETED:
        # delete this server
        op_api.do_delete_server(instance)
        waiter.wait_server_deleted(instance['op_server_id'],
                                   timeout=WAIT_DELETE_SERVER_TIMEOUT)

        # if the server has boot volume, delete the volume.
        # for old instances, which boot from image needn't erase volume
        if (instance['op_volume_id'] and
           not instance['op_volume_id'].startswith('dummy')):
            op_api.do_delete_boot_volume(instance)

        Instance.update(instance_id, **{
            'status': INSTANCE_STATUS_CEASED,
            'ceased': datetime.datetime.utcnow(),
        })
    else:
        logger.warn('instance status is not DELETED, can not be ceased!')
        logger.warn('STRANGE, it should not enter .erase method!')
