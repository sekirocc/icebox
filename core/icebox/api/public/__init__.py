from densefog import web
from icebox.api import guard
from icebox.api import middleware

import volume as volume_api
# import snapshot as snapshot_api
import key_pair as key_pair_api
import eip as eip_api
import network as network_api
import instance as instance_api
import instance_type as instance_type_api
import image as image_api
import monitor as monitor_api
import job as job_api
import project as project_api
import operation as operation_api


def w(f):
    @web.stat_user_access
    @web.guard_generic_failure
    @web.guard_provider_failure
    @web.guard_resource_failure
    @web.guard_params_failure
    @guard.guard_explicit_code_failure
    @guard.guard_project_failure
    @guard.guard_access_key_failure
    @guard.guard_auth_failure
    @middleware.load_access_key
    @middleware.load_project
    def inner():
        return f()

    return inner


switch = {
    # eips
    'DescribeEips': w(eip_api.describe_eips),
    'AllocateEips': w(eip_api.allocate_eips),
    'UpdateBandwidth': w(eip_api.update_bandwidth),
    'ReleaseEips': w(eip_api.release_eips),
    'ModifyEipAttributes': w(eip_api.modify_eip_attributes),
    'AssociateEip': w(eip_api.associate_eip),
    'DissociateEips': w(eip_api.dissociate_eips),
    # key_pairs
    'DescribeKeyPairs': w(key_pair_api.describe_key_pairs),
    'CreateKeyPair': w(key_pair_api.create_key_pair),
    'DeleteKeyPairs': w(key_pair_api.delete_key_pairs),
    'ModifyKeyPairAttributes': w(key_pair_api.modify_key_pair_attributes),
    # networks
    'DescribeNetworks': w(network_api.describe_networks),
    'CreateNetwork': w(network_api.create_network),
    'DeleteNetworks': w(network_api.delete_networks),
    'ModifyNetworkAttributes': w(network_api.modify_network_attributes),
    'SetExternalGateway': w(network_api.set_external_gateway),
    'UpdateExternalGatewayBandwidth': w(network_api.update_external_gateway_bandwidth),  # noqa
    'UnsetExternalGateway': w(network_api.unset_external_gateway),
    'DescribeSubnets': w(network_api.describe_subnets),
    'CreateSubnet': w(network_api.create_subnet),
    'DeleteSubnets': w(network_api.delete_subnets),
    'ModifySubnetAttributes': w(network_api.modify_subnet_attributes),
    'DescribePortForwardings': w(network_api.describe_port_forwardings),
    'CreatePortForwarding': w(network_api.create_port_forwarding),
    'DeletePortForwardings': w(network_api.delete_port_forwardings),
    'ModifyPortForwardingAttributes': w(network_api.modify_port_forwarding_attributes),  # noqa
    # instances
    'DescribeInstances': w(instance_api.describe_instances),
    'CreateInstances': w(instance_api.create_instances),
    'StartInstances': w(instance_api.start_instances),
    'StopInstances': w(instance_api.stop_instances),
    'RestartInstances': w(instance_api.restart_instances),
    'ResetInstances': w(instance_api.reset_instances),
    'ResizeInstances': w(instance_api.resize_instances),
    'DeleteInstances': w(instance_api.delete_instances),
    'CaptureInstance': w(instance_api.capture_instance),
    'ChangePassword': w(instance_api.change_password),
    'ChangeKeyPair': w(instance_api.change_key_pair),
    'ModifyInstanceAttributes': w(instance_api.modify_instance_attributes),
    'ConnectVNC': w(instance_api.connect_vnc),
    'GetInstanceOutput': w(instance_api.get_instance_output),
    # instance_types
    'DescribeInstanceTypes': w(instance_type_api.describe_instance_types),
    # jobs
    'DescribeJobs': w(job_api.describe_jobs),
    # projects
    'DescribeQuotas': w(project_api.describe_quotas),
    # images
    'DescribeImages': w(image_api.describe_images),
    'DeleteImages': w(image_api.delete_images),
    'ModifyImageAttributes': w(image_api.modify_image_attributes),
    # volumes
    'DescribeVolumes': w(volume_api.describe_volumes),
    'CreateVolumes': w(volume_api.create_volumes),
    'DeleteVolumes': w(volume_api.delete_volumes),
    'AttachVolume': w(volume_api.attach_volume),
    'DetachVolumes': w(volume_api.detach_volumes),
    'ExtendVolumes': w(volume_api.extend_volumes),
    'ModifyVolumeAttributes': w(volume_api.modify_volume_attributes),
    # volumes
    # 'DescribeSnapshots': w(snapshot_api.describe_snapshots),
    # 'CreateSnapshots': w(snapshot_api.create_snapshots),
    # 'DeleteSnapshots': w(snapshot_api.delete_snapshots),
    # 'ModifySnapshotAttributes': w(snapshot_api.modify_snapshot_attributes),
    # load balancer
    # monitor
    'GetMonitor': w(monitor_api.get_monitor),
    # operation
    'DescribeOperations': w(operation_api.describe_operations),
}
