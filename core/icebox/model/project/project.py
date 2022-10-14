import datetime
import traceback
from densefog import db
from densefog.model import base
from densefog.model import filters
from icebox.model.project import error
from icebox.model.iaas import error as iaas_error
from icebox.model.iaas.openstack import identify
from icebox.model.iaas.openstack import network
from icebox.model.iaas.openstack import compute
from icebox.model.iaas.openstack import block

from densefog import logger
logger = logger.getChild(__file__)

TENANT_STATUS_ACTIVE = 'active'
TENANT_STATUS_DELETED = 'deleted'


class Project(base.LockableModel):

    # TODO ???? what is this.
    # deletable = False

    @classmethod
    def db(cls):
        return db.DB.project

    def reload(self):
        return get(self['id'])

    def _check_quota(self, resource, want):
        qt_key = 'qt_' + resource
        cu_key = 'cu_' + resource

        quota = int(self[qt_key])
        used = int(self[cu_key])
        if quota - used < want:
            raise error.ResourceQuotaNotEnough(resource,
                                               quota,
                                               used,
                                               want)

    def must_have_enough_quota(self, resource, want):
        """
        User want to allocate some resource,
        then they must have enough quota for the resource.
        usage:
        project.must_have_enough_quota('instances', 5)
        means the project want to create 5 instances.
        """
        self = self.reload()

        self._check_quota(resource, want)

    def must_have_enough_quotas(self, **resource_wants):
        """
        bulk check.
        project.must_have_enough_quota(instances=5, volumes=2)
        """
        self = self.reload()

        for resource, want in resource_wants.items():
            self._check_quota(resource, want)

    def _update_current_used(self, **resource_deltas):
        updates = {
            'updated': datetime.datetime.utcnow(),
        }

        for resource, delta in resource_deltas.items():
            cu_key = 'cu_' + resource
            cu_val = Project.db().c[cu_key] + delta
            updates[cu_key] = cu_val
            logger.info('project (%s) resource (%s) quota current usage: %d' %
                        (self['id'], resource, self[cu_key] + delta))

        # atomic update
        Project.update(self['id'], **updates)

        self = self.reload()

    def consume_quota(self, resource, num):
        """
        Use consume some resource
        usage:
        project.consume_quota('instances', 5)
        meas project have created 5 instances.
        """
        self.consume_quotas(**{resource: num})

    def consume_quotas(self, **resource_nums):
        """
        User bulk consume some resources
        """
        resource_deltas = {}

        for resource, num in resource_nums.items():
            logger.info('project (%s) resource (%s) consume quota %d' %
                        (self['id'], resource, num))
            resource_deltas[resource] = num

        self._update_current_used(**resource_deltas)

    def release_quota(self, resource, num):
        """
        User free some resource
        usage:
        project.release_quota('instances', 5)
        meas project have deleted 5 instances.
        """
        self.release_quotas(**{resource: num})

    def release_quotas(self, **resource_nums):
        """
        User bulk free some resources
        """
        resource_deltas = {}

        for resource, num in resource_nums.items():
            logger.info('project (%s) resource (%s) release quota %d' %
                        (self['id'], resource, num))
            resource_deltas[resource] = -num

        self._update_current_used(**resource_deltas)

    def format_total_quota(self):
        self = self.reload()

        return {
            'instances': self['qt_instances'],
            'vcpus': self['qt_vcpus'],
            'memory': self['qt_memory'],
            'images': self['qt_images'],
            'eips': self['qt_eips'],
            'networks': self['qt_networks'],
            'volumes': self['qt_volumes'],
            'volumeSize': self['qt_volume_size'],
            'snapshots': self['qt_snapshots'],
            'keyPairs': self['qt_key_pairs'],
        }

    def format_usage_quota(self):
        self = self.reload()

        return {
            'instances': self['cu_instances'],
            'vcpus': self['cu_vcpus'],
            'memory': self['cu_memory'],
            'images': self['cu_images'],
            'eips': self['cu_eips'],
            'networks': self['cu_networks'],
            'volumes': self['cu_volumes'],
            'volumeSize': self['cu_volume_size'],
            'snapshots': self['cu_snapshots'],
            'keyPairs': self['cu_key_pairs'],
        }


def create(project_id,
           qt_instances,
           qt_vcpus,
           qt_memory,
           qt_images,
           qt_eips,
           qt_networks,
           qt_volumes,
           qt_volume_size,
           qt_snapshots,
           qt_key_pairs):

    logger.info('.create() start. ')

    # step 1. create project
    try:
        project = identify.create_project(name=project_id)
    except Exception as ex:
        stack = traceback.format_exc()  # noqa
        raise iaas_error.ProviderCreateProjectError(ex, stack)

    op_project_id = project['id']

    # step 2. add admin to the project
    try:
        identify.add_user_role(op_project_id)
    except Exception as ex:
        raise
        # stack = traceback.format_exc()  # noqa
        # raise iaas_error.ProviderAddUserRoleError(ex, stack)

    # step 3. set network quota for the project.
    try:
        network.update_quota(op_project_id,
                             floatingip=-1,
                             network=-1,
                             port=-1,
                             router=-1,
                             security_group=-1,
                             security_group_rule=-1,
                             subnet=-1,
                             subnetpool=-1)
    except Exception as ex:
        stack = traceback.format_exc()  # noqa
        raise iaas_error.ProviderUpdateNetworkQuotaError(ex, stack)

    # step 4. set compute quota for the project.
    try:
        compute.update_quota(op_project_id,
                             cores=-1,
                             fixed_ips=-1,
                             floating_ips=-1,
                             injected_file_content_bytes=-1,
                             injected_file_path_bytes=-1,
                             injected_files=-1,
                             instances=-1,
                             key_pairs=-1,
                             metadata_items=-1,
                             ram=-1,
                             security_group_rules=-1,
                             security_groups=-1,
                             server_group_members=-1,
                             server_groups=-1)
    except Exception as ex:
        stack = traceback.format_exc()  # noqa
        raise iaas_error.ProviderUpdateComputeQuotaError(ex, stack)

    # step 5. set block quota for the project.
    try:
        block.update_quota(op_project_id,
                           volumes=-1,
                           snapshots=-1,
                           gigabytes=-1)
    except Exception as ex:
        stack = traceback.format_exc()  # noqa
        raise iaas_error.ProviderUpdateBlockQuotaError(ex, stack)

    try:
        project_id = Project.insert(**{
            'id': project_id,
            'op_project_id': op_project_id,
            'qt_instances': qt_instances,
            'qt_vcpus': qt_vcpus,
            'qt_memory': qt_memory,
            'qt_images': qt_images,
            'qt_eips': qt_eips,
            'qt_networks': qt_networks,
            'qt_volumes': qt_volumes,
            'qt_volume_size': qt_volume_size,
            'qt_snapshots': qt_snapshots,
            'qt_key_pairs': qt_key_pairs,
            'cu_instances': 0,
            'cu_vcpus': 0,
            'cu_memory': 0,
            'cu_images': 0,
            'cu_eips': 0,
            'cu_networks': 0,
            'cu_volumes': 0,
            'cu_volume_size': 0,
            'cu_snapshots': 0,
            'cu_key_pairs': 0,
            'updated': datetime.datetime.utcnow(),
            'created': datetime.datetime.utcnow(),
        })
    except Exception as ex:
        if str(ex).find('Duplicate entry') != -1:
            raise error.ProjectDuplicated(project_id)
        else:
            raise

    logger.info('.create() OK. ')
    return project_id


def update(project_id, **kwargs):
    logger.info('.update() start. ')

    kwargs.update({
        'updated': datetime.datetime.utcnow()
    })
    Project.update(project_id, **kwargs)
    logger.info('.update() OK. ')


def get(project_id):
    logger.info('.get() start. ')
    project = Project.get_as_model(project_id)
    if project is None:
        raise error.ProjectNotFound(project_id)

    logger.info('.get() OK. ')
    return project


def limitation(project_ids=None, status=None,
               offset=0, limit=10, reverse=True):
    def where(t):
        _where = True
        _where = filters.filter_ids(_where, t, project_ids)
        _where = filters.filter_status(_where, t, status)
        return _where

    logger.info('.limitation() start. ')

    page = Project.limitation_as_model(where,
                                       offset=offset,
                                       limit=limit,
                                       order_by=filters.order_by(reverse))
    logger.info('.limitation() OK. ')

    return page
