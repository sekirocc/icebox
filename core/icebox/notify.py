import os
import json
import traceback
import urllib
import thread

from densefog.common import utils
from densefog.common import request
from densefog.model.job import job as job_model
from densefog.server.worker import JobNotifier

from icebox import config

from densefog import logger
logger = logger.getChild(__file__)


class JobFailSlackNotifier(JobNotifier):

    topic = job_model.NOTIFY_JOB_FAILED

    def call(self, job, exc_info, has_tried, is_last_chance):
        action = job['action']

        params = json.loads(job['params'])
        params_safe = utils.hide_secret(params)

        stack = traceback.format_exception(*exc_info)

        title = 'Job (%s) execution failed, trys: %d' % (job['id'], has_tried)
        send_to_slack(
            title,
            {
                'action': action,
                'params': params_safe,
                'exception': ''.join(stack),
            })


class JobFailSMSNotifier(JobNotifier):

    topic = job_model.NOTIFY_JOB_FAILED

    def call(self, job, exc_info, has_tried, is_last_chance):
        action = job['action']
        title = 'Job (%s) execution failed, trys: %d' % (job['id'], has_tried)
        send_to_sms(
            title,
            {
                'action': action,
                'exception': str(exc_info[0]),
            })


def send_to_slack(title, params):
    """
    send this title + params to slack channel.
    if there env variable SLACK_WEBHOOK_URL not exist, then do not send.
    """

    try:
        webhook_url = config.CONF.slack_webhook_url
        assert bool(webhook_url), 'slack_webhook_url is not set'
    except Exception as ex:
        logger.error(str(ex))
        logger.error('could not find slack webhook in config, will not notify to slack.')  # noqa
        return

    try:
        params['app'] = config.CONF.app_name
        params['host'] = get_host()
        text = [title] + ['%s: %s' % (k, v) for k, v in params.items()]
        text = '\n'.join(text)
        payload = {
            'payload': json.dumps({'text': text})
        }

        thread.start_new_thread(request.post, (
                                webhook_url,                # url
                                urllib.urlencode(payload),  # payload
                                {},                         # headers
                                logger,                     # logger
                                ))

    except Exception:
        stack = traceback.format_exc()
        logger.trace(stack)
        logger.error('unable to start notify thread')


def send_to_sms(title, params):
    """
    send this title + params to sms channel.
    it requires env variable
        NOTIFY_SMS_URL, NOTIFY_SMS_KEY, NOTIFY_SMS_SECRET, NOTIFY_SMS_MOBILES
    if either one is not set, do not send.
    """
    from densefog import logger

    try:
        sms_url = config.CONF.notify_sms_url
        sms_key = config.CONF.notify_sms_key
        sms_secret = config.CONF.notify_sms_secret
        sms_mobiles = config.CONF.notify_sms_mobiles

        assert bool(sms_url), 'notify_sms_url is not set'
        assert bool(sms_key), 'notify_sms_key is not set'
        assert bool(sms_secret), 'notify_sms_secret is not set'
        assert bool(sms_mobiles), 'notify_sms_mobiles is not set'
    except Exception as ex:
        logger.error(str(ex))
        logger.error('could not find sms config, will not notify to sms.')
        return

    try:
        params['app'] = config.CONF.app_name
        text = [title] + ['%s: %s' % (k, v) for k, v in params.items()]
        text = '\n'.join(text)

        payload = {
            'content': text,
            'tos': sms_mobiles,
        }

        headers = {
            'Content-Type': 'application/json',
            'X-Ice-Key': sms_key,
            'X-Ice-Secret': sms_secret,
        }

        thread.start_new_thread(request.post, (
                                sms_url,                # url
                                json.dumps(payload),    # payload
                                headers,                # headers
                                logger,                 # loggeer
                                ))

    except Exception:
        stack = traceback.format_exc()
        logger.trace(stack)
        logger.error('unable to start notify thread')


def get_host():
    host = os.uname()[1]
    try:
        return host.split('.')[0]
    except:
        return host
