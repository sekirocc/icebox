from densefog.error import BaseJobException
# from densefog.error import JobNotFound


class SyncResourceException(BaseJobException):
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __str__(self):
        msg = ["Sync resources failed because the FOLLOWING exceptions:"]
        for ex_dict in self.exceptions:
            ex = ex_dict['exception']
            msg.append('sync resource %s error: ' % ex_dict['resource'])
            msg.append(str(ex))

        msg = "\n".join(msg)
        return msg


class EraseResourceException(BaseJobException):
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __str__(self):
        msg = ["Erase resources failed because the FOLLOWING exceptions:"]
        for ex_dict in self.exceptions:
            ex = ex_dict['exception']
            msg.append('erase resource %s error: ' % ex_dict['resource'])
            msg.append(str(ex))

        msg = "\n".join(msg)
        return msg


class WatchedJobsFailedException(BaseJobException):
    def __init__(self, failed_jobs):
        self.failed_jobs = failed_jobs

    def __str__(self):
        msg = ["When watching other jobs, "
               "found FOLLOWING of them are failed: "]
        for job in self.failed_jobs:
            item = "job_id: %s, action: %s, resource_ids: %s" % (
                   job['id'], job['action'], job.get_resources())
            msg.append(item)

        msg = "\n".join(msg)
        return msg


class CreateBootVolumeImagesException(BaseJobException):
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __str__(self):
        msg = ["Create boot volume images failed because the FOLLOWING exceptions:"]  # noqa
        for ex_dict in self.exceptions:
            ex = ex_dict['exception']
            stack = ex_dict['stacktrace']
            msg.append(str(ex))
            msg.append(stack)

        msg = "\n".join(msg)
        return msg
