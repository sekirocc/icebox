import json
import time
import datetime
from densefog import db
from densefog.model import base
from icebox.model.project import project as project_model
from icebox.model.iaas import instance as instance_model
from icebox.model.iaas import volume as volume_model
from icebox.model.iaas import eip as eip_model
from icebox.model.iaas import network as network_model
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas.openstack import api as op_api

from densefog import logger
logger = logger.getChild(__file__)

MONITOR_PERIOD_120_MINS = '120mins'
MONITOR_PERIOD_720_MINS = '720mins'
MONITOR_PERIOD_48_HOURS = '48hours'
MONITOR_PERIOD_14_DAYS = '14days'
MONITOR_PERIOD_30_DAYS = '30days'

MONITOR_PERIODS = {
    MONITOR_PERIOD_120_MINS: [60, 120],
    MONITOR_PERIOD_720_MINS: [60 * 5, 144],
    MONITOR_PERIOD_48_HOURS: [60 * 15, 192],
    MONITOR_PERIOD_14_DAYS: [60 * 60 * 2, 168],
    MONITOR_PERIOD_30_DAYS: [60 * 60 * 12, 60],
}

MONITOR_METRIC_INSTANCE_CPU = 'instance.cpu'
MONITOR_METRIC_INSTANCE_MEMORY = 'instance.memory'
MONITOR_METRIC_INSTANCE_DISK_USAGE = 'instance.disk.usage'
MONITOR_METRIC_INSTANCE_DISK_IOPS = 'instance.disk.iops'
MONITOR_METRIC_INSTANCE_DISK_IO = 'instance.disk.io'
MONITOR_METRIC_INSTANCE_NETWORK_TRAFFIC = 'instance.network.traffic'
MONITOR_METRIC_INSTANCE_NETWORK_PACKETS = 'instance.network.packets'
MONITOR_METRIC_VOLUME_USAGE = 'volume.usage'
MONITOR_METRIC_VOLUME_IOPS = 'volume.iops'
MONITOR_METRIC_VOLUME_IO = 'volume.io'
MONITOR_METRIC_EIP_TRAFFIC = 'eip.traffic'
MONITOR_METRIC_EIP_PACKETS = 'eip.packets'

MONITOR_METRICS = {
    MONITOR_METRIC_INSTANCE_CPU: {
        'usage': ['cpu_util', 'avg'],
    },
    MONITOR_METRIC_INSTANCE_MEMORY: {
        'total': ['memory', 'avg'],
        'used': ['memory.usage', 'avg'],
    },
    MONITOR_METRIC_INSTANCE_DISK_USAGE: {
        'total': ['disk.capacity', 'avg'],
        'used': ['disk.allocation', 'avg'],
    },
    MONITOR_METRIC_INSTANCE_DISK_IOPS: {
        'read': ['disk.read.requests.rate', 'avg'],
        'write': ['disk.write.requests.rate', 'avg'],
    },
    MONITOR_METRIC_INSTANCE_DISK_IO: {
        'read': ['disk.read.bytes.rate', 'avg'],
        'write': ['disk.write.bytes.rate', 'avg'],
    },
    MONITOR_METRIC_INSTANCE_NETWORK_TRAFFIC: {
        'in': ['network.incoming.bytes.rate', 'avg'],
        'out': ['network.outgoing.bytes.rate', 'avg'],
    },
    MONITOR_METRIC_INSTANCE_NETWORK_PACKETS: {
        'in': ['network.incoming.packets.rate', 'avg'],
        'out': ['network.outgoing.packets.rate', 'avg'],
    },
    MONITOR_METRIC_VOLUME_USAGE: {
        'total': ['disk.device.capacity', 'avg'],
        'usage': ['disk.device.allocation', 'avg'],
    },
    MONITOR_METRIC_VOLUME_IOPS: {
        'read': ['disk.device.read.requests.rate', 'avg'],
        'write': ['disk.device.write.requests.rate', 'avg'],
    },
    MONITOR_METRIC_VOLUME_IO: {
        'read': ['disk.device.read.bytes.rate', 'avg'],
        'write': ['disk.device.write.bytes.rate', 'avg'],
    },
    MONITOR_METRIC_EIP_TRAFFIC: {
        'in': ['network.l3.bytes.rate', 'avg'],
        'out': ['network.l3.bytes.rate', 'avg'],
    },
    MONITOR_METRIC_EIP_PACKETS: {
        'in': ['network.l3.packets.rate', 'avg'],
        'out': ['network.l3.packets.rate', 'avg'],
    },
}


class Monitor(base.ProjectModel):

    @classmethod
    def db(cls):
        return db.DB.monitor

    def format(self):
        data = json.loads(self['data'])
        formated = {
            'resourceId': self['resource_id'],
            'metric': self['metric'],
            'period': self['period'],
            'interval': self['interval'],
            'timeSeries': data,
            'updated': self['updated'],
        }
        return formated


def get_monitor(resource_id, project_id, metric, period):
    logger.info('.get_monitor() begin')

    interval, steps = MONITOR_PERIODS[period]

    monitor = Monitor.first_as_model(lambda t: Monitor.and_(
        t.resource_id == resource_id,
        t.interval == interval,
        t.period == period,
        t.metric == metric))

    if monitor:
        monitor.must_belongs_project(project_id)

    now = datetime.datetime.utcnow()
    if monitor is None or \
       monitor['updated'] + datetime.timedelta(seconds=interval) < now:
        monitor = pre_aggregate_monitor(
            resource_id=resource_id,
            project_id=project_id,
            metric=metric,
            period=period)

    logger.info('.get_monitor() OK.')
    return monitor


def pre_aggregate_monitor(resource_id, project_id, metric, period):
    logger.info('.pre_aggregate_monitor() begin')

    if resource_id.startswith('i-'):
        op_resource_id = instance_model.get(resource_id)['op_server_id']
    elif resource_id.startswith('v-'):
        op_resource_id = volume_model.get(resource_id)['op_volume_id']
    elif resource_id.startswith('eip-'):
        op_resource_id = eip_model.get(resource_id)['op_floatingip_id']
    elif resource_id.startswith('net-'):
        op_resource_id = network_model.get(resource_id)['op_router_id']
    else:
        raise iaas_error.MonitorNotFound(resource_id)

    project = project_model.get(project_id)
    op_project_id = project['op_project_id']

    metrics = MONITOR_METRICS[metric]
    interval, steps = MONITOR_PERIODS[period]

    now = datetime.datetime.utcnow()
    end = int(time.mktime(now.timetuple())) / interval * interval
    start = end - interval * steps

    aggregate = {}

    timestamp = start
    while timestamp < end:
        t = datetime.datetime.fromtimestamp(timestamp).isoformat()
        aggregate.setdefault(t, {})['timestamp'] = t
        timestamp += interval

    for i, sub_metric in enumerate(metrics):
        meter, aggregation = metrics[sub_metric]

        if resource_id.startswith('net-') or resource_id.startswith('eip-'):
            if sub_metric == 'in':
                op_resource_id = '00' + op_resource_id[2:]
            else:
                op_resource_id = '01' + op_resource_id[2:]

        meter_aggregate = op_api.do_statistics(
            meter,
            op_resource_id,
            op_project_id,
            aggregation=aggregation,
            period=interval,
            start=datetime.datetime.fromtimestamp(start),
            end=datetime.datetime.fromtimestamp(end))

        for sample in meter_aggregate:
            timestamp = sample['period_start']
            aggregate.setdefault(timestamp, {})['timestamp'] = timestamp
            aggregate[timestamp][sub_metric] = sample['value']

    aggregate = sorted(aggregate.values(), key=lambda a: a['timestamp'])

    monitor = Monitor.first_as_model(lambda t: Monitor.and_(
        t.resource_id == resource_id,
        t.interval == interval,
        t.period == period,
        t.metric == metric))

    if monitor is None:
        monitor_id = Monitor.insert(**{
            'resource_id': resource_id,
            'project_id': project_id,
            'metric': metric,
            'period': period,
            'interval': interval,
            'data': json.dumps(aggregate),
            'updated': datetime.datetime.fromtimestamp(end),
            'created': datetime.datetime.utcnow(),
        })
    else:
        Monitor.update(
            id=monitor['id'],
            data=json.dumps(aggregate),
            updated=datetime.datetime.fromtimestamp(end),
        )
        monitor_id = monitor['id']

    logger.info('.pre_aggregate_monitor() OK.')

    return Monitor.get_as_model(monitor_id)
