from icebox import config

CONF = config.CONF

RESOURCE_TYPE_INSTANCE = 'vm'
RESOURCE_TYPE_VOLUME = 'disk'
RESOURCE_TYPE_BANDWIDTH = 'bw'


class BaseBiller(object):

    def __init__(self, api):
        self.api = api
        self.region = api.region

    def _format_resource_usage(self, usage):
        formatted = {'resourceId': usage['resource_id']}

        if 'resource_name' in usage:
            formatted['resourceName'] = usage['resource_name']
        if 'resource_usage' in usage:
            formatted['resourceUsage'] = usage['resource_usage']

        return formatted

    def create_resources(self,
                         project_id,
                         resource_type,
                         resource_flavor=None,
                         resource_usages=[]):

        assert bool(project_id), 'project_id is required'
        assert bool(resource_type), 'resource_type is required'
        assert bool(resource_usages), 'resource_usages is required'

        resource_usages = [self._format_resource_usage(ru)
                           for ru in resource_usages]

        # if we are in debug mode. project_id stick to test.
        project_id = 'test' if CONF.billing_debug else project_id

        body = {
            'action': 'CreateResources',
            'projectId': project_id,
            'resourceType': resource_type,
            'resourceUsages': resource_usages,
        }
        if self.region:
            body['regionId'] = self.region

        if resource_flavor:
            body['resourceFlavor'] = resource_flavor

        resp = self.api.post(body)
        if not resp:
            raise Exception('no response data received.')
        return resp

    def delete_resources(self, project_id, resource_ids):
        assert bool(project_id), 'project_id is required'
        assert bool(resource_ids), 'resource_ids is required'

        # if we are in debug mode. project_id stick to test.
        project_id = 'test' if CONF.billing_debug else project_id

        body = {
            'action': 'DeleteResources',
            'projectId': project_id,
            'resourceIds': resource_ids
        }

        resp = self.api.post(body)
        if not resp:
            raise Exception('no response data received.')
        return resp

    def modify_resource_attributes(self,
                                   project_id,
                                   resource_id,
                                   resource_flavor=None,
                                   resource_usage=None):

        assert bool(project_id), 'project_id is required'
        assert bool(resource_id), 'resource_id is required'

        # if we are in debug mode. project_id stick to test.
        project_id = 'test' if CONF.billing_debug else project_id

        body = {
            'action': 'ModifyResourceAttributes',
            'projectId': project_id,
            'resourceId': resource_id
        }

        if resource_flavor:
            body['resourceFlavor'] = resource_flavor
        if resource_usage:
            body['resourceUsage'] = resource_usage

        resp = self.api.post(body)
        if not resp:
            raise Exception('no response data received.')
        return resp
