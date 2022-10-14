from icebox.model.iaas import error


def actions_job(action, project_id, pendings, exceptions):
    """
    for async actions.

    do an action for multiple resource models.
    some may successfully go pending,
    while others got exceptions.

    for those successfully pending actions, contruct a job model,
    for those exceptions, raise a ActionsPartialSuccessError.

    params_key normally is 'resource_ids'.  volume_ids, instance_ids, etc.
    """

    from densefog.model.job import job as job_model
    from icebox import config

    job_id = None
    if pendings:
        job_id = job_model.create(
            action=action,
            project_id=project_id,
            try_period=config.CONF.try_period,
            params={
                'resource_ids': pendings
            }
        )

    if exceptions:
        raise error.ActionsPartialSuccessError(
            exceptions=exceptions,
            job_id=job_id
        )
    else:
        return job_id


def actions_result(results, exceptions):
    """
    for sync actions.

    do an action for multiple resource models.
    some may successfully got results,
    while others got exceptions.
    """

    if exceptions:
        raise error.ActionsPartialSuccessError(
            exceptions=exceptions,
            results=results
        )
    return results
