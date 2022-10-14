from densefog.common import utils
from icebox.model.job import error as job_error
from densefog import logger
logger = logger.getChild(__file__)


def _sync_resources(resource_model, resources, time_sleep):
    """
    sync resource status from iaas provider
    """
    exceptions = []
    while True:
        busy_resources = []
        for resource_id in resources:
            logger.info('resource_model.sync(%s) start' % resource_id)
            try:
                resource = resource_model.sync(resource_id)
            except Exception as ex:
                logger.error('resource_model.sync(%s) ERROR!' % resource_id)
                exceptions.append({
                    'exception': ex,
                    'resource': resource_id
                })

            else:
                if resource.is_busy():
                    logger.info('resource is still busy, '
                                'put back for next loop')
                    busy_resources.append(resource_id)
                else:
                    logger.info('resource_model.sync(%s) OK.' % resource_id)

        if busy_resources:
            resources = busy_resources
            time_sleep(2)
        else:
            break

    if exceptions:
        raise job_error.SyncResourceException(exceptions)


def _erase_resources(resource_model, resources, time_sleep):
    """
    erase resource from iaas provider
    """
    exceptions = []
    for resource_id in resources:
        logger.info('resource_model.erase(%s) start' % resource_id)
        try:
            resource_model.erase(resource_id)
        except Exception as ex:
            logger.error('resource_model.erase(%s) ERROR!' % resource_id)
            exceptions.append({
                'exception': ex,
                'resource': resource_id
            })

        else:
            logger.info('resource_model.erase(%s) OK.' % resource_id)

    if exceptions:
        raise job_error.EraseResourceException(exceptions)
    else:
        time_sleep(2)


def start_instances(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    instance_ids = params['resource_ids']
    _sync_resources(instance_model, instance_ids, time_sleep)


def stop_instances(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    instance_ids = params['resource_ids']
    _sync_resources(instance_model, instance_ids, time_sleep)


def create_instances(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    instance_ids = params['resource_ids']
    _sync_resources(instance_model, instance_ids, time_sleep)


def restart_instances(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    instance_ids = params['resource_ids']
    _sync_resources(instance_model, instance_ids, time_sleep)


def resize_instances(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    instance_ids = params['resource_ids']
    _sync_resources(instance_model, instance_ids, time_sleep)


def capture_instances(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    instance_ids = params['resource_ids']
    _sync_resources(instance_model, instance_ids, time_sleep)


def sync_instances(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    instance_ids = params['resource_ids']
    _sync_resources(instance_model, instance_ids, time_sleep)


def create_images(params, time_sleep, is_last_chance):
    from icebox.model.iaas import image as image_model
    image_ids = params['resource_ids']
    _sync_resources(image_model, image_ids, time_sleep)


def sync_images(params, time_sleep, is_last_chance):
    from icebox.model.iaas import image as image_model
    image_ids = params['resource_ids']
    _sync_resources(image_model, image_ids, time_sleep)


def create_volumes(params, time_sleep, is_last_chance):
    from icebox.model.iaas import volume as volume_model
    volume_ids = params['resource_ids']
    _sync_resources(volume_model, volume_ids, time_sleep)


def attach_volumes(params, time_sleep, is_last_chance):
    from icebox.model.iaas import volume as volume_model
    volume_ids = params['resource_ids']
    _sync_resources(volume_model, volume_ids, time_sleep)


def detach_volumes(params, time_sleep, is_last_chance):
    from icebox.model.iaas import volume as volume_model
    volume_ids = params['resource_ids']
    _sync_resources(volume_model, volume_ids, time_sleep)


def extend_volumes(params, time_sleep, is_last_chance):
    from icebox.model.iaas import volume as volume_model
    volume_ids = params['resource_ids']
    _sync_resources(volume_model, volume_ids, time_sleep)


def sync_volumes(params, time_sleep, is_last_chance):
    from icebox.model.iaas import volume as volume_model
    volume_ids = params['resource_ids']
    _sync_resources(volume_model, volume_ids, time_sleep)


def create_snapshots(params, time_sleep, is_last_chance):
    from icebox.model.iaas import snapshot as snapshot_model
    snapshot_ids = params['resource_ids']
    _sync_resources(snapshot_model, snapshot_ids, time_sleep)


def create_networks(params, time_sleep, is_last_chance):
    from icebox.model.iaas import network as network_model
    network_ids = params['resource_ids']
    _sync_resources(network_model, network_ids, time_sleep)


def sync_networks(params, time_sleep, is_last_chance):
    from icebox.model.iaas import network as network_model
    network_ids = params['resource_ids']
    _sync_resources(network_model, network_ids, time_sleep)


def erase_eips(params, time_sleep, is_last_chance):
    from icebox.model.iaas import eip as eip_model
    eip_ids = params['resource_ids']
    _erase_resources(eip_model, eip_ids, time_sleep)


def erase_images(params, time_sleep, is_last_chance):
    from icebox.model.iaas import image as image_model
    image_ids = params['resource_ids']
    _erase_resources(image_model, image_ids, time_sleep)


def erase_instances(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    instance_ids = params['resource_ids']
    _erase_resources(instance_model, instance_ids, time_sleep)


def erase_instance_types(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance_type as instance_type_model
    instance_type_ids = params['resource_ids']
    _erase_resources(instance_type_model, instance_type_ids, time_sleep)


def erase_key_pairs(params, time_sleep, is_last_chance):
    from icebox.model.iaas import key_pair as key_pair_model
    key_pair_ids = params['resource_ids']
    _erase_resources(key_pair_model, key_pair_ids, time_sleep)


def erase_networks(params, time_sleep, is_last_chance):
    from icebox.model.iaas import network as network_model
    network_ids = params['resource_ids']
    _erase_resources(network_model, network_ids, time_sleep)


def erase_snapshots(params, time_sleep, is_last_chance):
    from icebox.model.iaas import snapshot as snapshot_model
    snapshot_ids = params['resource_ids']
    _erase_resources(snapshot_model, snapshot_ids, time_sleep)


def erase_subnets(params, time_sleep, is_last_chance):
    from icebox.model.iaas import subnet as subnet_model
    subnet_ids = params['resource_ids']
    _erase_resources(subnet_model, subnet_ids, time_sleep)


def erase_port_forwardings(params, time_sleep, is_last_chance):
    from icebox.model.iaas import port_forwarding as port_forwarding_model  # noqa
    port_forwarding_ids = params['resource_ids']
    _erase_resources(port_forwarding_model, port_forwarding_ids, time_sleep)


def erase_volumes(params, time_sleep, is_last_chance):
    from icebox.model.iaas import volume as volume_model
    volume_ids = params['resource_ids']
    _erase_resources(volume_model, volume_ids, time_sleep)


def sync(params, time_sleep, is_last_chance):
    pass


def sync_floatingips(params, time_sleep, is_last_chance):
    from icebox.model.iaas import floatingip as floatingip_model
    floatingip_model.sync_all()


def create_image(params, time_sleep, is_last_chance):
    from icebox.model.iaas import image as image_model
    # extract create arguments.
    args = params['args']

    image_id = args['image_id']
    instance_id = args['instance_id']

    logger.info('create_image for %s' % image_id)

    try:
        image_model.create_image(image_id, instance_id)
    except:
        if is_last_chance:
            image_model.create_image_failed(image_id)
        raise


def create_server(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    # extract create arguments.
    args = params['args']

    instance_id = args['instance_id']
    key_pair_id = args['key_pair_id']
    login_password = args['login_password']
    ip_address = args['ip_address']
    user_data = args['user_data']

    logger.info('create_server for %s' % instance_id)

    try:
        instance_model.create_server(instance_id,
                                     key_pair_id,
                                     login_password,
                                     ip_address,
                                     user_data)
    except:
        if is_last_chance:
            instance_model.create_server_failed(instance_id)
        raise


@utils.footprint(logger)
def rebuild_server(params, time_sleep, is_last_chance):
    from icebox.model.iaas import instance as instance_model
    # extract build arguments.
    args = params['args']

    instance_id = args['instance_id']
    image_id = args['image_id']
    key_pair_id = args['key_pair_id']
    login_password = args['login_password']

    logger.info('rebuild_server for %s' % instance_id)

    try:
        instance_model.rebuild_server(instance_id,
                                      image_id,
                                      key_pair_id,
                                      login_password)
    except:
        if is_last_chance:
            instance_model.rebuild_server_failed(instance_id)
        raise


def watching_jobs(params, time_sleep, is_last_chance):
    """Wathcing some jobs.
    watching untill all of them finished or errored.

    """
    from densefog.model.job import job as job_model

    error_jobs = []
    resources = params['job_ids']
    while True:
        busy_jobs = []
        for job_id in resources:
            job = job_model.get(job_id)

            logger.info('watching job (%s) start' % job_id)
            if job.is_finished():
                logger.info('watched job(%s) is finished, OK.' % job_id)
            elif job.is_error():
                logger.info('watched job(%s) is failed, OK.' % job_id)
                error_jobs.append(job)
            else:
                logger.debug('watched job(%s) is still busy, keep watch' % job_id)  # noqa
                busy_jobs.append(job_id)

        if busy_jobs:
            resources = busy_jobs
            time_sleep(2)
        else:
            break

    if error_jobs:
        raise job_error.WatchedJobsFailedException(error_jobs)
