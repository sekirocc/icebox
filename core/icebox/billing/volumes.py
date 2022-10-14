import traceback
from icebox.billing.biller import BaseBiller
from icebox.billing.biller import RESOURCE_TYPE_VOLUME

from densefog import logger
logger = logger.getChild(__file__)


class VolumeBiller(BaseBiller):

    def _collect_usages(self, project_id, volume_ids):
        from icebox.model.iaas import volume as volume_model
        page = volume_model.limitation(project_ids=[project_id],
                                       volume_ids=volume_ids)
        volumes = page['items']

        resource_usages = []
        for volume in volumes:
            resource_usages.append({
                'resource_id': volume['id'],
                'resource_name': volume['name'],
                'resource_usage': '%dGB' % volume['size'],
            })
        return resource_usages

    def create_volumes(self, project_id, volume_ids):
        logger.info('biller to create volumes: %s' % volume_ids)

        if not project_id or not volume_ids:
            return

        resource_usages = self._collect_usages(project_id, volume_ids)

        try:
            resp = self.create_resources(project_id,
                                         RESOURCE_TYPE_VOLUME,
                                         None,
                                         resource_usages)
            logger.info('create_resources resp code: %s, message: %s' % (
                        resp['retCode'], resp['message']))
            return resp

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)
        pass

    def delete_volumes(self, project_id, volume_ids):
        logger.info('biller to delete volumes: %s' % volume_ids)

        if not project_id or not volume_ids:
            return

        try:
            resp = self.delete_resources(project_id, volume_ids)

            logger.info('delete_resources resp code: %s, message: %s' % (
                        resp['retCode'], resp['message']))
            return resp

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)

    def resize_volumes(self, project_id, volume_ids):
        logger.info('biller to resize volumes: %s' % volume_ids)

        if not project_id or not volume_ids:
            return

        resource_usages = self._collect_usages(project_id, volume_ids)

        try:
            resps = []
            for resource_usage in resource_usages:
                resource_id = resource_usage['resource_id']
                usage = resource_usage['resource_usage']
                resp = self.modify_resource_attributes(project_id,
                                                       resource_id,
                                                       None,
                                                       usage)

                logger.info('modify_resource_attributes resp code: %s, '
                            'message: %s' % (resp['retCode'], resp['message']))
                resps.append(resp)

            return resps

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)
