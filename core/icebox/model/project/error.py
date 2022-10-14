
class BaseProjectException(Exception):
    def __str__(self):
        return self.message


class BaseAccessKeyException(BaseProjectException):
    pass


class AccessKeyDuplicated(BaseAccessKeyException):
    def __init__(self, key):
        self.key = key
        self.message = 'Access key (%s) already exists' % key


class AccessKeyExpired(BaseAccessKeyException):
    def __init__(self, key):
        self.key = key
        self.message = 'Authorization failed. you access key (%s) is expired' % key   # noqa


class AccessKeyInvalid(BaseAccessKeyException):
    def __init__(self, key):
        self.key = key
        self.message = 'Authorization failed. your access key (%s) is invalid.' % key   # noqa


class ManageAccessKeyInvalid(BaseAccessKeyException):
    def __init__(self, key):
        self.key = key
        self.message = 'Manage authorization failed. manage access key (%s) is invalid.' % key   # noqa


class AccessKeyNotFound(BaseAccessKeyException):
    def __init__(self, key):
        self.key = key
        self.message = 'Access key (%s) is not found' % key


class ProjectDuplicated(BaseProjectException):
    def __init__(self, project_id):
        self.project_id = project_id
        self.message = 'Project (%s) alreay exists.' % project_id


class ProjectNotFound(BaseProjectException):
    def __init__(self, project_id):
        self.project_id = project_id
        self.message = 'Project (%s) is not found.' % project_id


class ResourceQuotaNotEnough(BaseProjectException):
    def __init__(self, resource, quota, used, want):
        self.resource = resource
        self.quota = quota
        self.used = used
        self.want = want
        self.message = 'Project quota[%s] not enough: want [%d], but have [%d]' % (    # noqa
            resource, want, (quota - used)
        )
