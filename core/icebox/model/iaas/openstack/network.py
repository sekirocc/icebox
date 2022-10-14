from neutronclient.v2_0 import client as neutron_client
from icebox.model.iaas.openstack import constants
from icebox.model.iaas.openstack import identify
from icebox.model.iaas.openstack import cache_openstack_client

NET_STATUS_ACTIVE = 'ACTIVE'
NET_STATUS_BUILD = 'BUILD'
NET_STATUS_DOWN = 'DOWN'
NET_STATUS_ERROR = 'ERROR'

PORT_STATUS_ACTIVE = 'ACTIVE'
PORT_STATUS_BUILD = 'BUILD'
PORT_STATUS_DOWN = 'DOWN'
PORT_STATUS_ERROR = 'ERROR'
PORT_STATUS_NOTAPPLICABLE = 'N/A'

FLOATINGIP_STATUS_ACTIVE = 'ACTIVE'
FLOATINGIP_STATUS_DOWN = 'DOWN'
FLOATINGIP_STATUS_ERROR = 'ERROR'

ROUTER_STATUS_ACTIVE = 'ACTIVE'
ROUTER_STATUS_ALLOCATING = 'ALLOCATING'


@cache_openstack_client('network')
def client():
    session = identify.client().session
    client = neutron_client.Client(session=session)
    client.lbaas_listeners_path = "/lbaasv3/listeners"
    client.lbaas_listener_path = "/lbaasv3/listeners/%s"
    client.lbaas_l7policies_path = "/lbaasv3/l7policies"
    client.lbaas_pools_path = "/lbaasv3/pools"
    client.lbaas_pool_path = "/lbaasv3/pools/%s"
    client.lbaas_healthmonitors_path = "/lbaasv3/healthmonitors"
    client.lbaas_healthmonitor_path = "/lbaasv3/healthmonitors/%s"
    client.lbaas_members_path = client.lbaas_pool_path + "/members"
    client.lbaas_member_path = client.lbaas_pool_path + "/members/%s"

    return client


def _extract_router(r):
    return {
        'id': r['id'],
        'name': r['name'],
        'description': r['description'],
        'admin_state_up': r['admin_state_up'],
        'availability_zone_hints': r['availability_zone_hints'],
        'availability_zones': r['availability_zones'],
        'distributed': r['distributed'],
        'external_gateway_info': r['external_gateway_info'],
        'portforwardings': r['portforwardings'],
        'ha': r['ha'],
        'routes': r['routes'],
        'status': r['status'],
        'project_id': r['tenant_id']
    }


def create_router(project_id, name):
    c = client()
    body_sample = {
        'router': {
            'name': '%s%s' % (constants.NAME_PREFIX, name),
            'tenant_id': project_id,
            'admin_state_up': True
        }
    }
    r = c.create_router(body=body_sample)['router']
    return _extract_router(r)


def set_gateway_router(router_id, rate_limit):
    c = client()
    public_network = get_public_network()

    body_sample = {
        'network_id': public_network['id'],
        'rate_limit': rate_limit,
    }
    r = c.add_gateway_router(router_id, body=body_sample)['router']
    return _extract_router(r)


def remove_gateway_router(router_id):
    c = client()
    r = c.remove_gateway_router(router_id)['router']
    return _extract_router(r)


def delete_router(router_id):
    c = client()
    c.delete_router(router_id)


def get_router(router_id):
    c = client()
    r = c.list_routers(id=router_id)['routers'][0]
    return _extract_router(r)


def list_routers(project_id=None):
    c = client()
    filters = {}
    if project_id:
        filters['tenant_id'] = project_id
    routers = c.list_routers(**filters)['routers']
    return [_extract_router(r) for r in routers
            if r['name'].startswith(constants.NAME_PREFIX)]


def update_quota(project_id, floatingip, network,
                 port, router, security_group, security_group_rule,
                 subnet, subnetpool):
    c = client()
    body_sample = {
        'quota': {
            'floatingip': floatingip,
            'network': network,
            'rbac_policy': 10,
            'port': port,
            'router': router,
            'security_group': security_group,
            'security_group_rule': security_group_rule,
            'subnet': subnet,
            'subnetpool': subnetpool
        }
    }
    q = c.update_quota(project_id, body=body_sample)['quota']
    return {
        'floatingip': q['floatingip'],
        'network': q['network'],
        'port': q['port'],
        'router': q['router'],
        'security_group': q['security_group'],
        'security_group_rule': q['security_group_rule'],
        'subnet': q['subnet'],
        'subnetpool': q['subnetpool']
    }


def _extract_port(p):
    return {
        'admin_state_up': p['admin_state_up'],
        'allowed_address_pairs': p['allowed_address_pairs'],
        'binding:host_id': p['binding:host_id'],
        'binding:profile': p['binding:profile'],
        'binding:vif_details': p['binding:vif_details'],
        'binding:vif_type': p['binding:vif_type'],
        'binding:vnic_type': p['binding:vnic_type'],
        'created_at': p['created_at'],
        'description': p['description'],
        'device_id': p['device_id'],
        'device_owner': p['device_owner'],
        'dns_name': p['dns_name'],
        'extra_dhcp_opts': p['extra_dhcp_opts'],
        'fixed_ips': p['fixed_ips'],
        'id': p['id'],
        'mac_address': p['mac_address'],
        'name': p['name'],
        'network_id': p['network_id'],
        'security_groups': p['security_groups'],
        'status': p['status'],
        'project_id': p['tenant_id'],
        'updated_at': p['updated_at']
    }


def create_port(project_id, network_id, subnet_id, ip_address=None):
    c = client()
    fixed_ip = {
        'subnet_id': subnet_id,
    }
    if ip_address:
        fixed_ip['ip_address'] = ip_address

    body_sample = {
        'port': {
            'tenant_id': project_id,
            'network_id': network_id,
            'fixed_ips': [fixed_ip],
        }
    }
    p = c.create_port(body=body_sample)['port']
    return _extract_port(p)


def list_ports(network_id=None, subnet_id=None):
    c = client()

    filters = {}
    if network_id:
        filters['network_id'] = network_id
    if subnet_id:
        filters['subnet_id'] = subnet_id

    ports = c.list_ports(**filters)['ports']
    return [_extract_port(p) for p in ports]


def get_port(port_id=None):
    c = client()

    p = c.show_port(port_id)['port']
    return _extract_port(p)


def delete_port(port_id):
    c = client()
    c.delete_port(port_id)


def _extract_subnet(n):
    return {
        'id': n['id'],
        'name': n['name'],
        'allocation_pools': n['allocation_pools'],
        'cidr': n['cidr'],
        'created_at': n['created_at'],
        'description': n['description'],
        'dns_nameservers': n['dns_nameservers'],
        'enable_dhcp': n['enable_dhcp'],
        'gateway_ip': n['gateway_ip'],
        'host_routes': n['host_routes'],
        'ip_version': n['ip_version'],
        'ipv6_address_mode': n['ipv6_address_mode'],
        'ipv6_ra_mode': n['ipv6_ra_mode'],
        'network_id': n['network_id'],
        'subnetpool_id': n['subnetpool_id'],
        'project_id': n['tenant_id'],
        'updated_at': n['updated_at']
    }


def create_subnet(project_id, network_id, name, cidr):
    c = client()
    body_sample = {
        'subnet': {
            'name': '%s%s' % (constants.NAME_PREFIX, name),
            'cidr': cidr,
            'network_id': network_id,
            'tenant_id': project_id,
            'enable_dhcp': False,
            'dns_nameservers': ['8.8.8.8', '8.8.4.4'],
            'ip_version': 4,
        }
    }
    n = c.create_subnet(body=body_sample)['subnet']
    return _extract_subnet(n)


def attach_subnet(subnet_id, router_id):
    c = client()
    c.add_interface_router(router_id, {
        'subnet_id': subnet_id,
    })


def detach_subnet(subnet_id, router_id):
    c = client()
    c.remove_interface_router(router_id, {
        'subnet_id': subnet_id,
    })


def delete_subnet(subnet_id):
    c = client()
    c.delete_subnet(subnet_id)


def list_subnets(network_id=None, is_public=True):
    c = client()
    filters = {
        'ip_version': 4,
    }
    if network_id:
        filters['network_id'] = network_id

    subnets = c.list_subnets(**filters)['subnets']

    if is_public:
        filtered = [_extract_subnet(n) for n in subnets]
    else:
        filtered = [_extract_subnet(n) for n in subnets
                    if n['name'].startswith(constants.NAME_PREFIX)]
    return filtered


def _extract_network(n):
    return {
        'id': n['id'],
        'name': n['name'],
        'status': n['status'],
        'subnets': n['subnets'],
        'created_at': n['created_at'],
        'updated_at': n['updated_at'],
        'project_id': n['tenant_id'],
        'admin_state_up': n['admin_state_up'],
        'availability_zone_hints': n['availability_zone_hints'],
        'availability_zones': n['availability_zones'],
        'description': n['description'],
        'ipv4_address_scope': n['ipv6_address_scope'],
        'ipv6_address_scope': n['ipv6_address_scope'],
        'mtu': n['mtu'],
        'provider:network_type': n['provider:network_type'],
        'provider:physical_network': n['provider:physical_network'],
        'provider:segmentation_id': n['provider:segmentation_id'],
        'router:external': n['router:external'],
        'shared': n['shared'],
        'tags': n['tags'],
    }


def create_network(project_id, name):
    c = client()
    body_sample = {
        'network': {
            'name': '%s%s' % (constants.NAME_PREFIX, name),
            'tenant_id': project_id,
            'admin_state_up': True
        }
    }
    n = c.create_network(body=body_sample)['network']
    return _extract_network(n)


def delete_network(network_id):
    c = client()
    c.delete_network(network_id)


def get_network(network_id=None):
    c = client()
    n = c.list_networks(id=network_id)['networks'][0]
    return _extract_network(n)


def list_networks(project_id=None):
    c = client()
    filters = {}
    if project_id:
        filters['tenant_id'] = project_id
    networks = c.list_networks(**filters)['networks']
    return [_extract_network(n) for n in networks
            if n['name'].startswith(constants.NAME_PREFIX)]


def get_public_network():
    c = client()
    filters = {
        'router:external': True
    }

    ret = c.list_networks(**filters)
    if not (ret and ret['networks']):
        return None

    n = ret['networks'][0]
    return _extract_network(n)


def _extract_floatingip(f):
    return {
        'id': f['id'],
        'description': f['description'],
        'status': f['status'],
        'project_id': f['tenant_id'],
        'floating_ip_address': f['floating_ip_address'],
        'floating_network_id': f['floating_network_id'],
        'router_id': f['router_id'],
        'port_id': f['port_id'],
        'fixed_ip_address': f['fixed_ip_address'],
    }


def create_floatingip(project_id, rate_limit):
    c = client()
    public_network = get_public_network()
    body_sample = {
        'floatingip': {
            'tenant_id': project_id,
            'description': '%s%s' % (constants.NAME_PREFIX, 'floatingip'),
            'floating_network_id': public_network['id'],
            'rate_limit': rate_limit,
        }
    }
    f = c.create_floatingip(body=body_sample)['floatingip']
    return _extract_floatingip(f)


def delete_floatingip(floatingip_id):
    c = client()
    c.delete_floatingip(floatingip_id)


def update_floatingip_port(floatingip_id, port_id=None):
    """
    if port exists, means associate floatingip with port
    if port is None, means dissociate floatingip from port
    """
    c = client()
    body_sample = {
        'floatingip': {
            'port_id': port_id
        }
    }
    c.update_floatingip(floatingip_id, body=body_sample)


def update_floatingip_rate_limit(floatingip_id, rate_limit):
    c = client()
    body_sample = {
        'floatingip': {
            'rate_limit': rate_limit
        }
    }
    c.update_floatingip(floatingip_id, body=body_sample)


def list_floatingips(project_id=None):
    c = client()

    filters = {}
    if project_id:
        filters['tenant_id'] = project_id

    floatingips = c.list_floatingips(**filters)['floatingips']
    return [_extract_floatingip(f) for f in floatingips
            if f['description'].startswith(constants.NAME_PREFIX)]


def _extract_port_forwarding(pf):
    return {
        'id': pf['id'],
        'inside_address': pf['inside_addr'],
        'inside_port': pf['inside_port'],
        'outside_port': pf['outside_port'],
        'protocol': pf['protocol'],
        'router_id': pf['router_id'],
    }


def add_port_forwarding(router_id, protocol, outside_port,
                        inside_address, inside_port):
    c = client()
    body = {
        'protocol': protocol,
        'inside_addr': inside_address,
        'outside_port': outside_port,
        'inside_port': inside_port,
    }
    router_path = c.router_path % (router_id)
    pf = c.put(router_path + '/add_router_portforwarding', body=body)
    return _extract_port_forwarding(pf)


def remove_port_forwarding(router_id, port_forwarding_id):
    c = client()
    body = {
        'id': port_forwarding_id,
    }
    router_path = c.router_path % (router_id)
    return c.put(router_path + '/remove_router_portforwarding', body=body)
