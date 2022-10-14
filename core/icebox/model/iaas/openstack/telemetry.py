from ceilometerclient import client as ceilometer_client
from icebox.model.iaas.openstack import identify
from icebox.model.iaas.openstack import cache_openstack_client


@cache_openstack_client('telemetry')
def client(project_id=None):
    session = identify.client(project_id).session
    c = ceilometer_client.get_client(2, session=session)
    return c


def list_meters(resource_id):
    c = client()
    meters = c.meters.list(q=[{
        'field': 'resource_id',
        'op': 'eq',
        'value': resource_id
    }], limit=100)
    return [{
        'meter_id': m.meter_id,
        'name': m.name,
        'project_id': m.project_id,
        'resource_id': m.resource_id,
        'source': m.source,
        'type': m.type,
        'unit': m.unit,
        'user_id': m.user_id
    } for m in meters]


def list_samples(meter, resource_id):
    c = client()
    samples = c.new_samples.list(q=[{
        'field': 'meter',
        'op': 'eq',
        'value': meter,
    }, {
        'field': 'resource_id',
        'op': 'eq',
        'value': resource_id,
    }], limit=100)
    return [{
        'meter': m.meter,
        'project_id': m.project_id,
        'recorded_at': m.recorded_at,
        'resource_id': m.resource_id,
        'source': m.source,
        'timestamp': m.timestamp,
        'type': m.type,
        'unit': m.unit,
        'user_id': m.user_id,
        'volume': m.volume,
    } for m in samples]


def statistics(meter, resource_id, project_id,
               aggregation, period, start, end):
    c = client()
    statistics = c.statistics.list(
        meter_name=meter,
        q=[{
            'field': 'resource_id',
            'op': 'eq',
            'value': resource_id,
        }, {
            'field': 'project_id',
            'op': 'eq',
            'value': project_id,
        }, {
            'field': 'timestamp',
            'op': 'gt',
            'value': start
        }, {
            'field': 'timestamp',
            'op': 'lt',
            'value': end
        }],
        period=period,
        aggregates=[{
            'func': aggregation
        }])
    return [{
        'value': s.aggregate[aggregation],
        'duration': s.duration,
        'duration_end': s.duration_end,
        'duration_start': s.duration_start,
        'groupby': s.groupby,
        'period': s.period,
        'period_end': s.period_end,
        'period_start': s.period_start,
        'unit': s.unit
    } for s in statistics]
