import traceback
from icebox.billing.biller import BaseBiller
from icebox.billing.biller import RESOURCE_TYPE_BANDWIDTH

from densefog import logger
logger = logger.getChild(__file__)


class EipBiller(BaseBiller):

    def _collect_usages(self, project_id, eip_ids):
        from icebox.model.iaas import eip as eip_model
        page = eip_model.limitation(project_ids=[project_id],
                                    eip_ids=eip_ids)
        eips = page['items']

        resource_usages = []
        for eip in eips:
            resource_usages.append({
                'resource_id': eip['id'],
                'resource_name': eip['name'],
                'resource_usage': '%dMbps' % eip['bandwidth'],
            })
        return resource_usages

    def allocate_eips(self, project_id, eip_ids):
        logger.info('biller to allocate eips: %s' % eip_ids)

        if not project_id or not eip_ids:
            return

        resource_usages = self._collect_usages(project_id, eip_ids)

        try:
            resp = self.create_resources(project_id,
                                         RESOURCE_TYPE_BANDWIDTH,
                                         None,
                                         resource_usages)
            logger.info('create_resources resp code: %s, message: %s' % (
                        resp['retCode'], resp['message']))
            return resp

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)
        pass

    def release_eips(self, project_id, eip_ids):
        logger.info('biller to delete eips: %s' % eip_ids)

        if not project_id or not eip_ids:
            return

        try:
            resp = self.delete_resources(project_id, eip_ids)

            logger.info('delete_resources resp code: %s, message: %s' % (
                        resp['retCode'], resp['message']))
            return resp

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)

    def update_bandwidth(self, project_id, eip_ids):
        logger.info('biller to update brandwidth eips: %s' % eip_ids)

        if not project_id or not eip_ids:
            return

        resource_usages = self._collect_usages(project_id, eip_ids)

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
