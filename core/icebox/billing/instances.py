import traceback
from icebox.billing.biller import BaseBiller
from icebox.billing.biller import RESOURCE_TYPE_INSTANCE

from icebox import config

from densefog import logger
logger = logger.getChild(__file__)

resource_flavors = set(config.CONF.billing_flavors.split(','))


def map_to_flavor(instance_type_id):
    from icebox.model.iaas import instance_type as instance_type_model
    instance_type = instance_type_model.get(instance_type_id)

    # XcXg format
    composed = '%dc%dg' % (instance_type['vcpus'],
                           instance_type['memory'] / 1024)

    if composed not in resource_flavors:
        return None
    return composed


class InstanceBiller(BaseBiller):

    def _collect_usages(self, project_id, instance_ids):
        from icebox.model.iaas import instance as instance_model
        page = instance_model.limitation(project_ids=[project_id],
                                         instance_ids=instance_ids)
        instances = page['items']

        resource_usages = []
        for instance in instances:
            resource_usages.append({
                'resource_id': instance['id'],
                'resource_name': instance['name'],
            })

        return resource_usages

    def create_instances(self, project_id, instance_type_id, instance_ids):
        logger.info('biller to create instances: %s' % instance_ids)

        if not project_id or not instance_ids:
            return

        resource_flavor = map_to_flavor(instance_type_id)
        if not resource_flavor:
            logger.error('instance type can\'t be mapped to resource flavor!')
            return

        resource_usages = self._collect_usages(project_id, instance_ids)

        try:
            resp = self.create_resources(project_id,
                                         RESOURCE_TYPE_INSTANCE,
                                         resource_flavor,
                                         resource_usages)
            logger.info('create_resources resp code: %s, message: %s' % (
                        resp['retCode'], resp['message']))
            return resp

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)

    def delete_instances(self, project_id, instance_ids):
        logger.info('biller to delete instances: %s' % instance_ids)

        if not project_id or not instance_ids:
            return

        try:
            resp = self.delete_resources(project_id, instance_ids)

            logger.info('delete_resources resp code: %s, message: %s' % (
                        resp['retCode'], resp['message']))
            return resp

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)

    def resize_instances(self, project_id, instance_type_id, instance_ids):
        logger.info('biller to resize instances: %s' % instance_ids)

        if not project_id or not instance_ids:
            return

        resource_flavor = map_to_flavor(instance_type_id)
        if not resource_flavor:
            logger.error('instance type can\'t be mapped to resource flavor!')
            return

        resource_usages = self._collect_usages(project_id, instance_ids)

        try:
            resps = []
            for resource_usage in resource_usages:
                resource_id = resource_usage['resource_id']
                resp = self.modify_resource_attributes(project_id,
                                                       resource_id,
                                                       resource_flavor,
                                                       None)

                logger.info('modify_resource_attributes resp code: %s, '
                            'message: %s' % (resp['retCode'], resp['message']))
                resps.append(resp)

            return resps

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)
