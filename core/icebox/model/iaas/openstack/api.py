import traceback
from icebox.model.iaas.openstack import compute as compute_provider
from icebox.model.iaas.openstack import network as network_provider
from icebox.model.iaas.openstack import block as block_provider
from icebox.model.iaas.openstack import image as image_provider
from icebox.model.iaas.openstack import telemetry as telemetry_provider
from icebox.model.iaas.openstack import error as op_error
from icebox.model.iaas import error as iaas_error
from densefog.common import utils

from densefog import logger
logger = logger.getChild(__file__)


##################################################################
#
#  instance related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_create_boot_volume(op_project_id, op_image_id, size, name=None):
    # size = 1  # TODO. DELETE ME!
    try:
        name = name or 'boot-volume'
        volume = block_provider.create_volume(size,
                                              name,
                                              project_id=op_project_id,
                                              image_ref=op_image_id)
        logger.info('op api created volume, id: %s, host: %s, status: %s' % (
                    volume['id'], volume['host'], volume['status']))

        return volume

    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateBootVolumeError(ex, stack)


@utils.footprint(logger)
def do_create_data_volume(op_project_id, size, name, volume_type, snapshot_id):
    # size = 1  # TODO. DELETE ME!
    try:
        volume = block_provider.create_volume(size,
                                              name,
                                              project_id=op_project_id,
                                              volume_type=volume_type,
                                              snapshot_id=snapshot_id)
        logger.info('op api created volume, id: %s, host: %s, status: %s' % (
                    volume['id'], volume['host'], volume['status']))

        return volume

    except Exception as ex:
        if op_error.is_overlimit(ex):
            # resource pool is draining.  WARN administrator IMMEDIALTELY!
            # TODO!!!
            logger.error('provider pool is draning. %s' % ex)

        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateVolumeError(ex, stack)


@utils.footprint(logger)
def do_create_port(op_project_id, op_network_id, op_subnet_id, ip_address=None):  # noqa
    try:
        return network_provider.create_port(op_project_id,
                                            op_network_id,
                                            op_subnet_id,
                                            ip_address)
    except Exception as e:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreatePortError(e, stack)


@utils.footprint(logger)
def do_create_server(op_project_id, name, op_volume_id, op_flavor_id,
                     op_network_id, op_port_id,
                     key_pair_id, login_password,
                     user_data):

    # TODO. TINY CORE FLATOR.
    # op_flavor_id = 'd039bd3f-58bd-4754-92ce-e0219606d243'  # DELETE ME!

    nics = [{
        'net-id': op_network_id,
        'port-id': op_port_id
    }]
    bdm = [{
        'uuid': op_volume_id,
        'source_type': 'volume',
        'destination_type': 'volume',
        'boot_index': 0,
        'delete_on_termination': False  # we'd rather delete volume by hand
    }]

    try:
        server = compute_provider.create_server(op_project_id,
                                                name,
                                                image_id=None,
                                                flavor_id=op_flavor_id,
                                                nics=nics,
                                                key_name=key_pair_id,
                                                user_data=user_data,
                                                password=login_password,
                                                block_device_mapping_v2=bdm)
        logger.info('op api created server, id: %s, host: %s, status: %s' % (
                    server['id'], server['host'], server['status']))

        return server

    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateServerError(ex, stack)


@utils.footprint(logger)
def do_delete_port(instance=None, op_port_id=None):
    op_port_id = op_port_id or instance['op_port_id']

    try:
        network_provider.delete_port(op_port_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            stack = traceback.format_exc()
            raise iaas_error.ProviderDeletePortError(ex, stack)


def do_interface_detach(instance):
    try:
        compute_provider.interface_detach(instance['op_server_id'],
                                          instance['op_port_id'])
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            stack = traceback.format_exc()
            raise iaas_error.ProviderInterfaceDetachError(ex, stack)


def do_get_server(op_server_id):
    try:
        return compute_provider.get_server(op_server_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderGetServerError(ex, stack)


@utils.footprint(logger)
def do_stop_server(instance):
    try:
        compute_provider.stop_server(instance['op_server_id'])
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderStopServerError(ex, stack)


@utils.footprint(logger)
def do_start_server(instance):
    try:
        compute_provider.start_server(instance['op_server_id'])
    except Exception as ex:
        if str(ex).find('in vm_state active') != -1:
            pass
        else:
            stack = traceback.format_exc()
            raise iaas_error.ProviderStartServerError(ex, stack)


@utils.footprint(logger)
def do_reboot_server(instance, restart_type):
    try:
        compute_provider.reboot_server(instance['op_server_id'],
                                       restart_type)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderRebootServerError(ex, stack)


@utils.footprint(logger)
def do_resize_server(instance, instance_type):
    op_server_id = instance['op_server_id']
    op_flavor_id = instance_type['op_flavor_id']

    # TODO. TINY CORE FLATOR.
    # op_flavor_id = 'd039bd3f-58bd-4754-92ce-e0219606d243'  # DELETE ME!

    try:
        compute_provider.resize_server(op_server_id,
                                       op_flavor_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderResizeServerError(ex, stack)


@utils.footprint(logger)
def do_confirm_resize_server(op_server_id):
    try:
        compute_provider.confirm_server_resize(op_server_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderConfirmResizeServerError(ex, stack)


@utils.footprint(logger)
def do_get_vnc_console(op_server_id):
    try:
        return compute_provider.get_vnc_console(op_server_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderGetVncConsoleError(ex, stack)


@utils.footprint(logger)
def do_get_console_output(op_server_id):
    try:
        return compute_provider.get_console_output(op_server_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderGetConsoleOutputError(ex, stack)


@utils.footprint(logger)
def do_change_keypair(instance, key_pair_id):
    try:
        compute_provider.change_keypair(instance['op_server_id'],
                                        key_pair_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderChangeKeyPairError(ex, stack)


@utils.footprint(logger)
def do_change_password(instance, login_password):
    try:
        compute_provider.change_password(instance['op_server_id'],
                                         login_password)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderChangePasswordError(ex, stack)


@utils.footprint(logger)
def do_delete_server(instance=None, op_server_id=None):
    op_server_id = op_server_id or instance['op_server_id']

    try:
        compute_provider.delete_server(op_server_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            trace = traceback.format_exc()
            raise iaas_error.ProviderDeleteServerError(ex, trace)


@utils.footprint(logger)
def do_delete_boot_volume(instance=None, op_volume_id=None):
    op_volume_id = op_volume_id or instance['op_volume_id']

    try:
        do_delete_volume(op_volume_id=op_volume_id)
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderDeleteBootVolumeError(ex, trace)


##################################################################
#
#  keypair related openstack api.
#
##################################################################

def do_create_keypair(op_project_id, name, public_key):
    try:
        kp = compute_provider.create_keypair(op_project_id, name, public_key)
        return kp
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateKeypairError(ex, stack)


def do_delete_keypair(key_pair_id):
    try:
        compute_provider.delete_keypair(key_pair_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            trace = traceback.format_exc()
            raise iaas_error.ProviderDeleteKeypairError(ex, trace)


##################################################################
#
#  volume related openstack api.
#
##################################################################


@utils.footprint(logger)
def do_delete_volume(volume=None, op_volume_id=None):
    op_volume_id = op_volume_id or volume['op_volume_id']

    try:
        block_provider.delete_volume(op_volume_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            trace = traceback.format_exc()
            raise iaas_error.ProviderDeleteVolumeError(ex, trace)


@utils.footprint(logger)
def do_get_volume(op_volume_id):
    try:
        return block_provider.get_volume(op_volume_id)
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderGetVolumeError(ex, trace)


@utils.footprint(logger)
def do_extend_volume(volume, new_size):
    try:
        block_provider.extend_volume(volume['op_volume_id'],
                                     new_size)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderExtendVolumeError(ex, stack)


@utils.footprint(logger)
def do_attach_volume(instance=None, volume=None,
                     op_server_id=None, op_volume_id=None):

    if not op_server_id:
        op_server_id = instance['op_server_id']
    if not op_volume_id:
        op_volume_id = volume['op_volume_id']

    try:
        compute_provider.create_server_volume(op_server_id, op_volume_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateServerVolumeError(ex, stack)


@utils.footprint(logger)
def do_detach_volume(instance=None, volume=None,
                     op_server_id=None, op_volume_id=None):

    if not op_server_id:
        op_server_id = instance['op_server_id']
    if not op_volume_id:
        op_volume_id = volume['op_volume_id']

    try:
        compute_provider.delete_server_volume(op_server_id, op_volume_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderDeleteServerVolumeError(ex, stack)


##################################################################
#
#  image related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_nova_create_image(op_project_id, op_server_id, name):
    try:
        op_image_id = compute_provider.create_image(op_project_id,
                                                    op_server_id,
                                                    name)
        return do_get_image(op_image_id)

    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateImageError(ex, stack)


@utils.footprint(logger)
def do_glance_create_image(project_id, name, min_disk, min_memory,
                           capshot_id, location):
    try:
        op_image = image_provider.create_image(project_id,
                                               name,
                                               min_disk,
                                               min_memory,
                                               capshot_id)
        op_image_id = op_image['id']
        image_provider.add_image_location(op_image_id, location)

        return do_get_image(op_image_id)

    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateImageError(ex, stack)


@utils.footprint(logger)
def do_list_images():
    try:
        return image_provider.list_images()
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderListImagesError(ex, trace)


@utils.footprint(logger)
def do_get_image(op_image_id):
    try:
        return image_provider.get_image(op_image_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderGetImageError(ex, stack)


@utils.footprint(logger)
def do_delete_image(op_image_id):
    try:
        image_provider.delete_image(op_image_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            stack = traceback.format_exc()
            raise iaas_error.ProviderCreateImageError(ex, stack)


##################################################################
#
#  capshot related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_create_capshot(op_project_id, op_snapshot_id):
    try:
        return block_provider.create_capshot(op_project_id,
                                             op_snapshot_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateCapshotError(ex, stack)


@utils.footprint(logger)
def do_delete_capshot(op_capshot_id):
    try:
        block_provider.delete_capshot(op_capshot_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            stack = traceback.format_exc()
            raise iaas_error.ProviderDeleteCapshotError(ex, stack)


##################################################################
#
#  snapshot related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_delete_snapshot(op_snapshot_id):
    try:
        block_provider.delete_snapshot(op_snapshot_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            stack = traceback.format_exc()
            raise iaas_error.ProviderDeleteSnapshotError(ex, stack)


##################################################################
#
#  network related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_create_router(op_project_id, name):
    try:
        router = network_provider.create_router(op_project_id, name)
        return router
    except Exception as e:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateRouterError(e, stack)


@utils.footprint(logger)
def do_create_network(op_project_id, name):
    try:
        network = network_provider.create_network(op_project_id, name)
        return network
    except Exception as e:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateNetworkError(e, stack)


@utils.footprint(logger)
def do_delete_router(op_router_id):
    try:
        network_provider.delete_router(op_router_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            stack = traceback.format_exc()
            raise iaas_error.ProviderDeleteRouterError(ex, stack)


@utils.footprint(logger)
def do_delete_network(op_network_id):
    try:
        network_provider.delete_network(op_network_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            stack = traceback.format_exc()
            raise iaas_error.ProviderDeleteNetworkError(ex, stack)


@utils.footprint(logger)
def do_set_gateway_router(op_router_id, rate_limit):
    try:
        router = network_provider.set_gateway_router(op_router_id, rate_limit)
        return router
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderAddGatewayRouterError(ex, stack)


@utils.footprint(logger)
def do_remove_gateway_router(op_router_id):
    try:
        network_provider.remove_gateway_router(op_router_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderRemoveGatewayRouterError(ex, stack)


@utils.footprint(logger)
def do_get_network(op_network_id):
    try:
        network = network_provider.get_network(op_network_id)
        return network
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderGetNetworkError(ex, stack)


@utils.footprint(logger)
def do_get_router(op_router_id):
    try:
        router = network_provider.get_router(op_router_id)
        return router
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderGetRouterError(ex, stack)


@utils.footprint(logger)
def do_list_ports(op_network_id=None, op_subnet_id=None):
    try:
        ports = network_provider.list_ports(network_id=op_network_id,
                                            subnet_id=op_subnet_id)
        return ports
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderListPortsError(ex, stack)


##################################################################
#
#  subnet related openstack api.
#
##################################################################


@utils.footprint(logger)
def do_add_port_forwarding(op_router_id, protocol,
                           outside_port, inside_address, inside_port):
    try:
        pf = network_provider.add_port_forwarding(op_router_id,
                                                  protocol,
                                                  outside_port,
                                                  inside_address,
                                                  inside_port)
        return pf
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderAddPortForwardingError(ex, stack)


@utils.footprint(logger)
def do_remove_port_forwarding(op_router_id, op_port_forwarding_id):
    try:
        network_provider.remove_port_forwarding(op_router_id,
                                                op_port_forwarding_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            trace = traceback.format_exc()
            raise iaas_error.ProviderRemovePortForwardingError(ex, trace)


##################################################################
#
#  subnet related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_create_subnet(op_project_id, op_network_id, name, cidr):
    try:
        subnet = network_provider.create_subnet(op_project_id,
                                                op_network_id,
                                                name,
                                                cidr)
        return subnet

    except Exception as ex:
        if str(ex).find('overlaps with another subnet.') != -1:
            raise iaas_error.SubnetCreateDuplicatedCIDRError(cidr)
        if str(ex).find('is not a valid IP subnet.') != -1:
            raise iaas_error.SubnetCreateInvalidCIDRError(cidr)

        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateSubnetError(ex, stack)


@utils.footprint(logger)
def do_delete_subnet(op_subnet_id):
    try:
        network_provider.delete_subnet(op_subnet_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            trace = traceback.format_exc()
            raise iaas_error.ProviderDeleteSubnetError(ex, trace)


@utils.footprint(logger)
def do_detach_subnet(op_subnet_id, op_router_id):
    try:
        network_provider.detach_subnet(op_subnet_id, op_router_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            trace = traceback.format_exc()
            raise iaas_error.ProviderDetachSubnetError(ex, trace)


@utils.footprint(logger)
def do_attach_subnet(op_subnet_id, op_router_id):
    try:
        network_provider.attach_subnet(op_subnet_id, op_router_id)
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderAttachSubnetError(ex, trace)


##################################################################
#
#  floatingip related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_create_floatingip(op_project_id, rate_limit):
    try:
        fip = network_provider.create_floatingip(op_project_id, rate_limit)
        return fip
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderCreateFloatingipError(ex, stack)


@utils.footprint(logger)
def do_update_floatingip_rate_limit(op_floatingip_id, rate_limit):
    try:
        network_provider.update_floatingip_rate_limit(op_floatingip_id,
                                                      rate_limit)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderUpdateFloatingipError(ex, stack)


@utils.footprint(logger)
def do_update_floatingip_port(op_floatingip_id, op_port_id):
    try:
        network_provider.update_floatingip_port(op_floatingip_id,
                                                op_port_id)
    except Exception as ex:
        stack = traceback.format_exc()
        raise iaas_error.ProviderUpdateFloatingipPortError(ex, stack)


@utils.footprint(logger)
def do_delete_floatingip(op_floatingip_id):
    try:
        network_provider.delete_floatingip(op_floatingip_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            trace = traceback.format_exc()
            raise iaas_error.ProviderDeleteFloatingipError(ex, trace)


@utils.footprint(logger)
def do_list_floatingips():
    try:
        floatingip_infos = network_provider.list_floatingips()
        return floatingip_infos
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderListFloatingipsError(ex, trace)


@utils.footprint(logger)
def do_list_routers():
    try:
        routers = network_provider.list_routers()
        return routers
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderListRoutersError(ex, trace)


@utils.footprint(logger)
def do_get_public_network():
    try:
        net = network_provider.get_public_network()
        if not net:
            raise Exception('Public network is not found.')
        return net
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderGetPublicNetworkError(ex, trace)


@utils.footprint(logger)
def do_list_subnets(op_network_id, is_public):
    try:
        subnets = network_provider.list_subnets(op_network_id,
                                                is_public)
        return subnets
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderListSubnetsError(ex, trace)


##################################################################
#
#  floatingip related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_find_flavor(op_flavor_id):
    try:
        flavor = compute_provider.find_flavor(op_flavor_id)
        return flavor
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderFindFlavorError(ex, trace)


@utils.footprint(logger)
def do_create_flavor(name, ram, vcpus, disk, op_flavor_id):
    try:
        flavor = compute_provider.create_flavor(name, ram, vcpus, disk,
                                                op_flavor_id)
        return flavor
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderCreateFlavorError(ex, trace)


@utils.footprint(logger)
def do_update_flavor_quota(op_flavor_id,
                           disk_read_iops_sec,
                           disk_write_iops_sec,
                           disk_read_bytes_sec,
                           disk_write_bytes_sec,
                           vif_inbound_average,
                           vif_outbound_average):
    try:
        compute_provider.update_flavor_quota(op_flavor_id,
                                             disk_read_iops_sec,
                                             disk_write_iops_sec,
                                             disk_read_bytes_sec,
                                             disk_write_bytes_sec,
                                             vif_inbound_average,
                                             vif_outbound_average)
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderUpdateFlavorQuotaError(ex, trace)


@utils.footprint(logger)
def do_delete_flavor(op_flavor_id):
    try:
        compute_provider.delete_flavor(op_flavor_id)
    except Exception as ex:
        if op_error.is_notfound(ex):
            pass
        else:
            trace = traceback.format_exc()
            raise iaas_error.ProviderDeleteFlavorError(ex, trace)


##################################################################
#
#  hypervisors related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_list_hypervisors():
    try:
        hypervisors = compute_provider.list_hypervisors()
        return hypervisors

    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderListHypervisorsError(ex, trace)


##################################################################
#
#  hypervisors related openstack api.
#
##################################################################

@utils.footprint(logger)
def do_statistics(meter, op_resource_id, op_project_id, aggregation, period,
                  start, end):
    try:
        meter_aggregate = telemetry_provider.statistics(meter,
                                                        op_resource_id,
                                                        op_project_id,
                                                        aggregation,
                                                        period,
                                                        start,
                                                        end)
        return meter_aggregate
    except Exception as ex:
        trace = traceback.format_exc()
        raise iaas_error.ProviderStatisticsError(ex, trace)
