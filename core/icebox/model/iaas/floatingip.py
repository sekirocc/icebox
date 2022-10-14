import datetime
from densefog import db
from densefog.common import utils
from densefog.model import base
from densefog.model import filters
from icebox.model.iaas.openstack import api as op_api

from netaddr import IPRange

from densefog import logger
logger = logger.getChild(__file__)

FLOATINGIP_STATUS_ACTIVE = 'active'
FLOATINGIP_STATUS_DELETED = 'deleted'


class Floatingip(base.StatusModel):

    @classmethod
    def db(cls):
        return db.DB.floatingip


def create_ips(ips=None):
    ips = sorted(ips or [])
    logger.info('.create_ips() begin, total count: %s' % len(ips))

    createds = []
    for ip in ips:
        floatingip_id = 'fip-%s' % utils.generate_key(8)
        Floatingip.insert(**{
                          'id': floatingip_id,
                          'address': ip,
                          'status': FLOATINGIP_STATUS_ACTIVE,
                          'updated': datetime.datetime.utcnow(),
                          'created': datetime.datetime.utcnow()
                          })

        createds.append(floatingip_id)

    logger.info('.create_ips() OK.')

    return createds


def consume_ips(ips):
    ips = sorted(ips or [])
    logger.info('.consume_ips() begin, total count: %s' % len(ips))

    def update_any(ips):
        Floatingip.update_any(lambda t: t.address.in_(ips),
                              status=FLOATINGIP_STATUS_DELETED,
                              deleted=datetime.datetime.utcnow())

    # delete
    while len(ips) > 0:
        update_any(ips[0:20])
        ips = ips[20:]

    logger.info('.consume_ips() OK.')

    return True


def release_ips(ips):
    ips = sorted(ips or [])
    logger.info('.release_ips() begin, total count: %s' % len(ips))

    def update_any(ips):
        Floatingip.update_any(lambda t: t.address.in_(ips),
                              status=FLOATINGIP_STATUS_ACTIVE,
                              deleted=None,
                              updated=datetime.datetime.utcnow())

    # update to active
    while len(ips) > 0:
        update_any(ips[0:20])
        ips = ips[20:]

    logger.info('.release_ips() OK.')

    return True


# we do not support get api for now.
# def get(floatingip_id):
#     logger.info('.get() begin. floatingip_id: %s' % floatingip_id)

#     floatingip = Floatingip.get_as_model(floatingip_id)
#     if floatingip is None:
#         raise iaas_error.FloatingipNotFound(floatingip_id)

#     logger.info('.get() OK.')
#     return floatingip


def limitation(floating_ids=None, status=None, offset=0, limit=10):

    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, floating_ids)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() start')

    page = Floatingip.limitation_as_model(where,
                                          offset=offset,
                                          limit=limit)
    logger.info('.limitation() OK.')
    return page


def count(status=FLOATINGIP_STATUS_ACTIVE):
    logger.info('.count() begin')

    count = Floatingip.count(lambda t: t.status == status)

    logger.info('.count() OK. total %s %s floatingips.' % (count, status))
    return count


def sync_all():
    logger.info('.sync_all() begin.')

    # this contains all controlled floating ip address
    network_id = op_api.do_get_public_network()['id']
    subnets = op_api.do_list_subnets(op_network_id=network_id,
                                     is_public=True)

    # these routers are using some floating ip address.
    routers = op_api.do_list_routers()

    # these floating ip addresses are being used by eip.
    floatingip_infos = op_api.do_list_floatingips()

    page = Floatingip.limitation(limit=0, fields=['address', 'status'])
    old_ips = set([fip['address'] for fip in page['items']])

    # 1. get all controlled ips
    new_ips = set([])
    for subnet in subnets:
        for pool in subnet['allocation_pools']:
            for ip in IPRange(pool['start'], pool['end']):
                new_ips.add(str(ip))

    # 2. remove the routers used ips
    fixed_ip_infos = [r['external_gateway_info']['external_fixed_ips']
                      for r in routers if r['external_gateway_info']]
    for info in fixed_ip_infos:
        for item in info:
            new_ips.remove(str(item['ip_address']))

    # 3. move the eip used ips
    for info in floatingip_infos:
        new_ips.remove(info['floating_ip_address'])

    sam_ips = old_ips & new_ips

    del_ips = old_ips - sam_ips
    add_ips = new_ips - sam_ips

    # create new ips
    create_ips(list(add_ips))
    logger.info('create %s floatingips.' % len(add_ips))

    # delete old ips
    consume_ips(del_ips)
    logger.info('delete %s floatingips.' % len(del_ips))

    # activate old deleted ips
    act_ips = []
    for fip in page['items']:
        if (fip['address'] in sam_ips and
           fip['status'] == FLOATINGIP_STATUS_DELETED):
            act_ips.append(fip['address'])

    release_ips(list(act_ips))
    logger.info('activate %s floatingips.' % len(act_ips))

    logger.info('.sync_all() OK.')
