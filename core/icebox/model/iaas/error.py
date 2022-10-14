from densefog.error import BaseIaasException
from densefog.error import BaseResourceException           # noqa
from densefog.error import ResourceNotFound
from densefog.error import ResourceNotBelongsToProject     # noqa
from densefog.error import ResourceActionForbiden
from densefog.error import ResourceActionUnsupported
from densefog.error import InvalidRequestParameter
from densefog.error import ValidationError                 # noqa
from densefog.error import ResourceIsBusy                  # noqa
from densefog.error import ResourceIsDeleted               # noqa
from densefog.error import ResourceIsInError               # noqa
from densefog.error import ServerInternalError             # noqa
from densefog.error import IaasProviderActionError
from densefog.error import BaseWaiterError                 # noqa
from densefog.error import WaitObjectNotFound              # noqa
from densefog.error import WaitObjectInterrupt             # noqa
from densefog.error import WaitObjectTimeout               # noqa
from densefog.error import DBLockTimeoutError              # noqa


##################################################################
#
#  Not Found Exception Family
#
##################################################################

class NetworkNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Network (%s) is not found' % resource_id


class SubnetNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Subnet (%s) is not found' % resource_id


class FloatingipNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Floatingip (%s) is not found' % resource_id


class PortForwardingNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'PortForwarding (%s) is not found' % resource_id


class ImageNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Image (%s) is not found' % resource_id


class InstanceNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Instance (%s) is not found' % resource_id


class InstanceTypeNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'InstanceType (%s) is not found' % resource_id


class EipNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Eip (%s) is not found' % resource_id


class SubnetResourceNotFound(ResourceNotFound):
    def __init__(self, subnet_id, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Resource (%s) is not added to subnet (%s)' % (
            resource_id, subnet_id)


class EipResourceNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Eip (%s) is not associated to resource (%s)' % (
            resource_id[0], resource_id[1])


class KeyPairNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'KeyPair (%s) is not found' % resource_id


class VolumeNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Volume (%s) is not found' % resource_id


class InstanceVolumeNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Instance (%s) is not attached to volume (%s)' % (
            resource_id[0], resource_id[1])   # noqa


class SnapshotNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Snapshot (%s) is not found' % resource_id


class MonitorNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Monitor (%s) is not found' % resource_id


class HypervisorNotFound(ResourceNotFound):
    def __init__(self, resource_id):
        ResourceNotFound.__init__(self, resource_id)
        self.message = 'Hypervisor (%s) is not found' % resource_id


##################################################################
#
#  Action Unspported Exception Family
#
##################################################################


class InstanceResetUnsupported(ResourceActionUnsupported):
    def __init__(self, resource_id):
        ResourceActionUnsupported.__init__(self, resource_id)
        self.resource_id = resource_id
        self.message = 'Legacy instance (%s) reset is unsupported.' % resource_id  # noqa


class InstanceResizeUnsupported(ResourceActionUnsupported):
    def __init__(self, resource_id):
        ResourceActionUnsupported.__init__(self, resource_id)
        self.resource_id = resource_id
        self.message = 'Legacy instance (%s) resize is unsupported.' % resource_id  # noqa


class InstanceCreateImageUnsupported(ResourceActionUnsupported):
    def __init__(self, resource_id):
        ResourceActionUnsupported.__init__(self, resource_id)
        self.resource_id = resource_id
        self.message = 'Legacy instance (%s) capture image is unsupported.' % resource_id  # noqa


##################################################################
#
#  Action Forbiden Exception Family
#
##################################################################


class NetworkCanNotDelete(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete network (%s), '
                        'please check status') % resource_id


class SubnetCanNotDelete(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete subnet (%s), '
                        'please check status') % resource_id


class PortForwardingUnDeletableError(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete port forwarding (%s), '
                        'please check status') % resource_id


class ImageCanNotDelete(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete image (%s), '
                        'please check status') % resource_id


class ImageCanNotModify(ResourceActionForbiden):
    def __init__(self, resource_id, message=None):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = message or ('Can not modify image (%s), '
                                   'please check status') % resource_id


class ImageCanNotCreate(ResourceActionForbiden):
    def __init__(self, instance_id, message=None):
        ResourceActionForbiden.__init__(self, instance_id)
        self.message = message or ('Can not craete image, '
                                   'please check instance(%s) status') % instance_id   # noqa


class InstanceCanNotStart(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not start instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotStop(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not stop instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotDelete(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotBeAttached(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not attach to instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotBeDetached(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not detach from instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotBeAssociated(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not associated to instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotBeDissociated(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not dissociate from instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotRestart(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not restart instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotResize(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not resize instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotReset(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not reset instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotChangePassword(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not change password for instance (%s), '
                        'please check status') % resource_id


class InstanceCanNotChangeKeyPair(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not change key_pair for instance (%s), '
                        'please check status') % resource_id


class EipCanNotDelete(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete eip (%s), '
                        'please check status') % resource_id


class EipCanNotAssociate(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not associate eip (%s), '
                        'please check status') % resource_id


class EipCanNotDissociate(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not dissociate eip (%s), '
                        'please check status') % resource_id


class VolumeCanNotAttach(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not attach volume (%s), '
                        'please check status') % resource_id


class VolumeCanNotDetach(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not detach volume (%s), '
                        'please check status') % resource_id


class VolumeCanNotExtend(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not extend volume (%s), '
                        'please check status') % resource_id


class VolumeCanNotDelete(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete volume (%s), '
                        'please check status') % resource_id


class SnapshotCanNotDelete(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete snapshot (%s), '
                        'please check status') % resource_id


class SnapshotCanNotCreateVolume(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not create volume from snapshot (%s), '
                        'please check status') % resource_id


class KeyPairCanNotDelete(ResourceActionForbiden):
    def __init__(self, resource_id):
        ResourceActionForbiden.__init__(self, resource_id)
        self.message = ('Can not delete key_pair (%s), '
                        'please check status') % resource_id


##################################################################
#
#  Provider Error Family
#
##################################################################

class ProviderWaitSnapshotErrorStatus(IaasProviderActionError):
    pass


class ProviderWaitSnapshotStatusTimeout(IaasProviderActionError):
    pass


class ProviderWaitCapshotErrorStatus(IaasProviderActionError):
    pass


class ProviderWaitCapshotStatusTimeout(IaasProviderActionError):
    pass


class ProviderWaitVolumeErrorStatus(IaasProviderActionError):
    pass


class ProviderWaitVolumeStatusTimeout(IaasProviderActionError):
    pass


class ProviderWaitPortErrorStatus(IaasProviderActionError):
    pass


class ProviderWaitPortStatusTimeout(IaasProviderActionError):
    pass


class ProviderInvalidImageError(IaasProviderActionError):
    pass


class ProviderCreateFloatingipError(IaasProviderActionError):
    pass


class ProviderUpdateFloatingipError(IaasProviderActionError):
    pass


class ProviderUpdateFloatingipPortError(IaasProviderActionError):
    pass


class ProviderDeleteFloatingipError(IaasProviderActionError):
    pass


class ProviderListFloatingipsError(IaasProviderActionError):
    pass


class ProviderChangePasswordError(IaasProviderActionError):
    pass


class ProviderChangeKeyPairError(IaasProviderActionError):
    pass


class ProviderCreateImageError(IaasProviderActionError):
    pass


class ProviderGetImageError(IaasProviderActionError):
    pass


class ProviderCreateCapshotError(IaasProviderActionError):
    pass


class ProviderDeleteCapshotError(IaasProviderActionError):
    pass


class ProviderDeleteImageError(IaasProviderActionError):
    pass


class ProviderListImagesError(IaasProviderActionError):
    pass


class ProviderListHypervisorsError(IaasProviderActionError):
    pass


class ProviderInterfaceDetachError(IaasProviderActionError):
    pass


class ProviderCreatePortError(IaasProviderActionError):
    pass


class ProviderDeletePortError(IaasProviderActionError):
    pass


class ProviderCreateServerError(IaasProviderActionError):
    pass


class ProviderDeleteServerError(IaasProviderActionError):
    pass


class ProviderCreateBootVolumeError(IaasProviderActionError):
    pass


class ProviderDeleteBootVolumeError(IaasProviderActionError):
    pass


class ProviderGetServerError(IaasProviderActionError):
    pass


class ProviderWaitServerErrorStatus(IaasProviderActionError):
    pass


class ProviderConfirmResizeServerError(IaasProviderActionError):
    pass


class ProviderGetVncConsoleError(IaasProviderActionError):
    pass


class ProviderGetConsoleOutputError(IaasProviderActionError):
    pass


class ProviderStartServerError(IaasProviderActionError):
    pass


class ProviderStopServerError(IaasProviderActionError):
    pass


class ProviderRebootServerError(IaasProviderActionError):
    pass


class ProviderRebuildServerError(IaasProviderActionError):
    pass


class ProviderResizeServerError(IaasProviderActionError):
    pass


class ProviderCreateFlavorError(IaasProviderActionError):
    pass


class ProviderDeleteFlavorError(IaasProviderActionError):
    pass


class ProviderUpdateFlavorQuotaError(IaasProviderActionError):
    pass


class ProviderFindFlavorError(IaasProviderActionError):
    pass


class ProviderCreateKeypairError(IaasProviderActionError):

    def is_invalid(self):
        return str(self.exception).find('Keypair data is invalid') != -1


class ProviderDeleteKeypairError(IaasProviderActionError):
    pass


class ProviderCreateRouterError(IaasProviderActionError):
    pass


class ProviderCreateNetworkError(IaasProviderActionError):
    pass


class ProviderGetNetworkError(IaasProviderActionError):
    pass


class ProviderGetRouterError(IaasProviderActionError):
    pass


class ProviderDeleteNetworkError(IaasProviderActionError):
    pass


class ProviderGetPublicNetworkError(IaasProviderActionError):
    pass


class ProviderListSubnetsError(IaasProviderActionError):
    pass


class ProviderListPortsError(IaasProviderActionError):
    pass


class ProviderDeleteRouterError(IaasProviderActionError):
    pass


class ProviderListRoutersError(IaasProviderActionError):
    pass


class ProviderAddGatewayRouterError(IaasProviderActionError):
    pass


class ProviderRemoveGatewayRouterError(IaasProviderActionError):
    pass


class ProviderCreateSnapshotError(IaasProviderActionError):
    pass


class ProviderDeleteSnapshotError(IaasProviderActionError):
    pass


class ProviderCreateSubnetError(IaasProviderActionError):

    def is_dup_subnet(self):
        return str(self.exception).find('overlaps with another subnet.') != -1

    def is_invalid_cidr(self):
        return str(self.exception).find('is not a valid IP subnet.') != -1


class ProviderDetachSubnetError(IaasProviderActionError):
    pass


class ProviderDeleteSubnetError(IaasProviderActionError):
    pass


class ProviderDuplicatedSubnetError(ProviderCreateSubnetError):
    pass


class ProviderInvalidCIDRError(ProviderCreateSubnetError):
    pass


class ProviderAttachSubnetError(IaasProviderActionError):
    pass


class ProviderAddPortForwardingError(IaasProviderActionError):

    def is_invalid_port(self):
        return str(self.exception).find('Invalid port') != -1

    def not_match_subnets(self):
        return str(self.exception).find('does not match any subnets') != -1


class ProviderRemovePortForwardingError(IaasProviderActionError):
    pass


class ProviderCreateVolumeError(IaasProviderActionError):
    pass


class ProviderCreateServerVolumeError(IaasProviderActionError):
    pass


class ProviderDeleteServerVolumeError(IaasProviderActionError):
    pass


class ProviderExtendVolumeError(IaasProviderActionError):
    pass


class ProviderDeleteVolumeError(IaasProviderActionError):
    pass


class ProviderGetVolumeError(IaasProviderActionError):
    pass


class ProviderCreateProjectError(IaasProviderActionError):
    pass


class ProviderAddUserRoleError(IaasProviderActionError):
    pass


class ProviderUpdateNetworkQuotaError(IaasProviderActionError):
    pass


class ProviderUpdateComputeQuotaError(IaasProviderActionError):
    pass


class ProviderUpdateBlockQuotaError(IaasProviderActionError):
    pass


class ProviderStatisticsError(IaasProviderActionError):
    pass


##################################################################
#
#  Request Parameter Invalid Error Family
#
##################################################################

class InstanceLoginModeError(InvalidRequestParameter):
    def __init__(self):
        self.message = 'login mode is error.'

    def __str__(self):
        return self.message


class InstanceLoginPasswordWeak(InvalidRequestParameter):
    def __init__(self):
        self.message = 'password is too weak, at lease 8 charactors, mixed with number and letters.'  # noqa

    def __str__(self):
        return self.message


class InstanceNameTooComplex(InvalidRequestParameter):
    def __init__(self):
        self.message = 'instance name is too complex, only use numbers(0-9), letters(a-zA-Z), underscores(_), hyphens(-).'  # noqa

    def __str__(self):
        return self.message


class VolumeNewSizeTooSmall(InvalidRequestParameter):
    def __init__(self):
        self.message = 'new size is too small.'

    def __str__(self):
        return self.message


class VolumeCreateParamError(InvalidRequestParameter):
    def __init__(self):
        self.message = 'you must input either snapshot_id or volume_type when create volume.'  # noqa

    def __str__(self):
        return self.message


class VolumeCreateVolumeTypeNotSupportError(InvalidRequestParameter):
    def __init__(self):
        self.message = 'your volume type not supported.'

    def __str__(self):
        return self.message


class KeyPairCreateInvalidPublicKeyError(InvalidRequestParameter):
    def __init__(self):
        self.message = 'public key data is invalid.'

    def __str__(self):
        return self.message


class SubnetCreateInvalidCIDRError(InvalidRequestParameter):
    def __init__(self, cidr):
        self.cidr = cidr
        self.message = '%s is not a valid IP subnet.' % cidr

    def __str__(self):
        return self.message


class SubnetCreateDuplicatedCIDRError(InvalidRequestParameter):
    def __init__(self, cidr):
        self.cidr = cidr
        self.message = '%s overlaps with another subnet.' % cidr

    def __str__(self):
        return self.message


class PortForwardingInsideAddressNotInSubnetsError(InvalidRequestParameter):
    def __init__(self, inside_address):
        self.inside_address = inside_address
        self.message = ('Inside address %s does not match '
                        'any subnets in this router') % inside_address

    def __str__(self):
        return self.message


class PortForwardingOutsidePortUsedError(InvalidRequestParameter):
    def __init__(self, outside_port):
        self.outside_port = outside_port
        self.message = ('outside port %s has been used ' % outside_port)

    def __str__(self):
        return self.message


class PortForwardingPortInvalid(InvalidRequestParameter):
    def __init__(self, outside_port, inside_port):
        self.outside_port = outside_port
        self.inside_port = inside_port
        self.message = ('Port is invalid '
                        'should between 1 and 65535')

    def __str__(self):
        return self.message


##################################################################
#
#  Other Exceptions
#
##################################################################

class ActionsPartialSuccessError(BaseIaasException):
    """
    when process multiple action, some failed. some succeeded.
    failed actions must have `exceptions`
    but success actions still count, so for
    the success part.
        if it resulted a job, place job_id here.
        if it resulted some concret results, pass them to results param

    normally there will be either results or job_id. but not both.
    """
    def __init__(self, exceptions, results=[], job_id=None):
        self.exceptions = exceptions
        self.results = results
        self.job_id = job_id

    def __str__(self):
        msg = ["some actions failed because the FOLLOWING exceptions:"]
        for ex_dict in self.exceptions:
            ex = ex_dict['exception']
            msg.append(str(ex))

        msg = "\n".join(msg)
        return msg


##################################################################
#
#  Specific Iaas Error Family
#
##################################################################

class ExplicitCodeException(BaseIaasException):
    pass


class AssociateEipWithUnreachableInstance(ExplicitCodeException):
    def __init__(self, eip_id, network_id):
        self.eip_id = eip_id
        self.network_id = network_id
        self.message = "Eip (%s) can not reach instance's network (%s)" % (
            eip_id, network_id)


class ResetInstanceWithIllegalImage(ExplicitCodeException):
    def __init__(self, instance_id, image_id):
        self.instance_id = instance_id
        self.image_id = image_id
        self.message = ('Instance (%s) can not reset with illegal image (%s), '
                        'please check the image status.') % (
            instance_id, image_id)


class RemoveExternalGatewayWhenInstancesBindingEip(ExplicitCodeException):
    def __init__(self, instance_ids):
        self.instance_ids = instance_ids
        self.message = ('Network can not delete its external gateway '
                        'when there are instances still binding with eips')


class DeleteNetworkWhenInstancesInSubnet(ExplicitCodeException):
    def __init__(self, network_id):
        self.network_id = network_id
        self.message = ('Network (%s) can not be deleted '
                        'when instances still in its subnet') % (
            network_id)


class DeleteNetworkWhenResourcesInSubnet(ExplicitCodeException):
    def __init__(self, network_id):
        self.network_id = network_id
        self.message = ('Network (%s) can not be deleted '
                        'when loadbalancers still in it') % (
            network_id)


class DeleteNetworkWhenHasExternalGateway(ExplicitCodeException):
    def __init__(self, network_id):
        self.network_id = network_id
        self.message = ('Network (%s) can not be deleted '
                        'when it still has external gateway') % (
            network_id)


class DeleteSubnetWhenInstancesInSubnet(ExplicitCodeException):
    def __init__(self, subnet_id):
        self.subnet_id = subnet_id
        self.message = ('Subnet (%s) can not be deleted '
                        'when instances still in it') % (
            subnet_id)


class DeleteSubnetWhenResourcesInSubnet(ExplicitCodeException):
    def __init__(self, subnet_id):
        self.subnet_id = subnet_id
        self.message = ('Subnet (%s) can not be deleted '
                        'when loadbalancers still in it') % (
            subnet_id)


class CreateEipInsufficientFloatingip(ExplicitCodeException):
    def __init__(self, need, free):
        self.need = need
        self.free = free
        self.message = ('Eip can not be created, '
                        'free floating ips is insufficient. '
                        'you need %d, but there are %d left.' % (need, free))


class DetachVolumeWhenNotAttached(ExplicitCodeException):
    def __init__(self, volume_id, instance_id):
        self.volume_id = volume_id
        self.instance_id = instance_id
        self.message = ('Volume (%s) can not be detached from instance (%s) '
                        'when not attached before') % (
            volume_id, instance_id)


class DeleteInstanceWhenVolumesAttaching(ExplicitCodeException):
    def __init__(self, instance_id, volume_ids):
        self.instance_id = instance_id
        self.volume_ids = volume_ids
        self.message = ('Instance (%s) can not be delete, '
                        'it still has volumes (%s) attaching') % (
            instance_id, volume_ids)


class DeleteInstanceWhenEipAssociating(ExplicitCodeException):
    def __init__(self, instance_id, eip_id):
        self.instance_id = instance_id
        self.eip_id = eip_id
        self.message = ('Instance (%s) can not be delete, '
                        'it still has eip (%s) associating') % (
            instance_id, eip_id)


class CreateInstanceWhenFlavorTooSmall(ExplicitCodeException):
    def __init__(self, instance_type_id, image_id):
        self.instance_type_id = instance_type_id
        self.image_id = image_id
        self.message = ('Can not create instance, instance_type (%s) '
                        'is too small for image (%s)') % (
            instance_type_id, image_id)


class CreateInstanceWhenIpAddressNotValid(ExplicitCodeException):
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.message = ('Can not create instance, '
                        'ip address (%s) not valid ') % ip_address


class DeleteImagesWhenInstanceExists(ExplicitCodeException):
    def __init__(self, alive_instance_ids):
        self.alive_instance_ids = alive_instance_ids
        self.message = ('Can not delete images, some instances (%s) '
                        'are using these images.') % (
            alive_instance_ids)
