from densefog import web
from icebox.api import middleware
from icebox.api import guard

import project as project_api
import image as image_api
import instance_type as instance_type_api
import eip as eip_api
import instance as instance_api
import hypervisor as hypervisor_api
import network as network_api


def w(f):
    @web.stat_user_access
    @web.guard_generic_failure
    @web.guard_provider_failure
    @web.guard_resource_failure
    @web.guard_params_failure
    @guard.guard_project_failure
    @guard.guard_access_key_failure
    @guard.guard_auth_failure
    @middleware.load_access_key
    @middleware.check_manage
    def inner():
        return f()

    return inner


switch = {
    # project quota
    'UpsertQuotas': w(project_api.upsert_quota),
    # access_key
    'CreateAccessKeys': w(project_api.create_access_keys),
    'DeleteAccessKeys': w(project_api.delete_access_keys),
    # image
    'DescribeImages': w(image_api.describe_images),
    'SyncImages': w(image_api.sync_images),
    'ModifyImageAttributes': w(image_api.modify_image_attributes),
    'DeleteImages': w(image_api.delete_images),
    # instance_type
    'DescribeInstanceTypes': w(instance_type_api.describe_instance_types),
    'GenerateInstanceTypes': w(instance_type_api.generate_instance_types),
    'CreateInstanceType': w(instance_type_api.create_instance_type),
    'DeleteInstanceTypes': w(instance_type_api.delete_instance_types),
    # eips
    'DescribeEips': w(eip_api.describe_eips),
    # instances
    'DescribeInstances': w(instance_api.describe_instances),
    # hypervisor
    'DescribeHypervisors': w(hypervisor_api.describe_hypervisors),
    'ModifyHypervisorAttributes':
        w(hypervisor_api.modify_hypervisor_attributes),
    'SyncHypervisors': w(hypervisor_api.sync_hypervisors),
    # network
    'DescribeNetworks': w(network_api.describe_networks),
    'DescribeSubnets': w(network_api.describe_subnets),
    'AddSubnetResources': w(network_api.add_subnet_resources),
    'RemSubnetResources': w(network_api.rem_subnet_resources),
    'CountFloatingips': w(network_api.count_floatingips),
    'ConsumeFloatingips': w(network_api.consume_floatingips),
    'ReleaseFloatingips': w(network_api.release_floatingips),
}
