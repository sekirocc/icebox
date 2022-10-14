import traceback
import functools
from densefog.common.waiter import wait_object
from densefog.common.waiter import wait_deleted
from densefog import error

from densefog.common import utils
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas.openstack import block as block_provider
from icebox.model.iaas.openstack import network as network_provider
from icebox.model.iaas.openstack import compute as compute_provider

from densefog import logger
logger = logger.getChild(__file__)

WAITER_MAX_TIMEOUT = 60 * 60 * 24  # wait atmost 1 DAY.


@utils.footprint(logger)
def wait_volume_available(op_volume_id, timeout=10):
    fetcher = functools.partial(block_provider.get_volume, op_volume_id)
    predicate = lambda o: o['status'] == 'available'  # noqa
    interrupt = lambda o: o['status'] == 'error'  # noqa
    logger.info("op_volume_id: %s, timeout: %d" % (op_volume_id, timeout))
    try:
        return wait_object(fetcher, predicate, interrupt, timeout=timeout)
    except error.WaitObjectInterrupt as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitVolumeErrorStatus(ex, stack)

    except error.WaitObjectTimeout as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitVolumeStatusTimeout(ex, stack)


@utils.footprint(logger)
def wait_volume_inuse(op_volume_id, timeout=10):
    fetcher = functools.partial(block_provider.get_volume, op_volume_id)
    predicate = lambda o: o['status'] == 'in-use'  # noqa
    interrupt = lambda o: o['status'] == 'error'  # noqa
    logger.info("op_volume_id: %s, timeout: %d" % (op_volume_id, timeout))
    try:
        return wait_object(fetcher, predicate, interrupt, timeout=timeout)
    except error.WaitObjectInterrupt as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitVolumeErrorStatus(ex, stack)

    except error.WaitObjectTimeout as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitVolumeStatusTimeout(ex, stack)


@utils.footprint(logger)
def wait_port_available(op_port_id, timeout=10):
    fetcher = functools.partial(network_provider.get_port, op_port_id)
    predicate = lambda o: o['status'] == 'DOWN' and o['device_owner'] == ''  # noqa
    interrupt = lambda o: o['status'] == 'error'  # noqa
    logger.info("op_port_id: %s, timeout: %d" % (op_port_id, timeout))
    try:
        return wait_object(fetcher, predicate, interrupt, timeout=timeout)
    except error.WaitObjectInterrupt as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitPortErrorStatus(ex, stack)

    except error.WaitObjectTimeout as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitPortStatusTimeout(ex, stack)


@utils.footprint(logger)
def wait_capshot_available(op_capshot_id, timeout=10):
    fetcher = functools.partial(block_provider.get_capshot, op_capshot_id)
    predicate = lambda o: o['status'] == 'available'  # noqa
    interrupt = lambda o: o['status'] == 'error'  # noqa
    logger.info("op_capshot_id: %s, timeout: %d" % (op_capshot_id, timeout))
    try:
        return wait_object(fetcher, predicate, interrupt, timeout=timeout)
    except error.WaitObjectInterrupt as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitCapshotErrorStatus(ex, stack)

    except error.WaitObjectTimeout as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitCapshotStatusTimeout(ex, stack)


@utils.footprint(logger)
def wait_snapshot_available(op_snapshot_id, timeout=10):
    fetcher = functools.partial(block_provider.get_snapshot, op_snapshot_id)
    predicate = lambda o: o['status'] == 'available'  # noqa
    interrupt = lambda o: o['status'] == 'error'  # noqa
    logger.info("op_snapshot_id: %s, timeout: %d" % (op_snapshot_id, timeout))
    try:
        return wait_object(fetcher, predicate, interrupt, timeout=timeout)
    except error.WaitObjectInterrupt as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitSnapshotErrorStatus(ex, stack)

    except error.WaitObjectTimeout as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitSnapshotStatusTimeout(ex, stack)


@utils.footprint(logger)
def wait_server_available(op_server_id, timeout=0):
    fetcher = functools.partial(compute_provider.get_server, op_server_id)
    predicate = lambda o: o['vm_state'] and o['status'].lower() == 'active'  # noqa
    interrupt = lambda o: 'error' in o['vm_state']  # noqa
    logger.info("op_server_id: %s, timeout: %d" % (op_server_id, timeout))
    try:
        return wait_object(fetcher, predicate, interrupt, timeout=timeout)
    except error.WaitObjectInterrupt as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitServerErrorStatus(ex, stack)

    except error.WaitObjectTimeout as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitServerStatusTimeout(ex, stack)


@utils.footprint(logger)
def wait_server_deleted(op_server_id, timeout=0):
    fetcher = functools.partial(compute_provider.get_server, op_server_id)
    logger.info("op_server_id: %s, timeout: %d" % (op_server_id, timeout))
    try:
        return wait_deleted(fetcher, timeout=timeout)

    except error.WaitObjectTimeout as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitServerStatusTimeout(ex, stack)


@utils.footprint(logger)
def wait_port_deleted(op_port_id, timeout=0):
    fetcher = functools.partial(network_provider.get_port, op_port_id)
    logger.info("op_port_id: %s, timeout: %d" % (op_port_id, timeout))
    try:
        return wait_deleted(fetcher, timeout=timeout)

    except error.WaitObjectTimeout as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderWaitPortStatusTimeout(ex, stack)
