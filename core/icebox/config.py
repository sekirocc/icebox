
import os
from densefog import config

CONF = None


def setup(gevent=False, region=None):
    global CONF

    CONF = config.setup(gevent)

    if not region:
        region = os.getenv('REGION_ID')

    settings = {
        'debug': os.getenv('DEBUG') == 'True',

        'region': region,
        'gevent': gevent,

        'public_port': int(os.getenv('PUBLIC_PORT') or 9000),
        'manage_port': int(os.getenv('MANAGE_PORT') or 9001),
        'manage_key': os.getenv('MANAGE_KEY'),
        'manage_secret': os.getenv('MANAGE_SECRET'),

        # openstack
        'op_keystone_endpoint': os.getenv('OPENSTACK_KEYSTONE_ENDPOINT'),
        'op_admin_name': os.getenv('OPENSTACK_ADMIN_NAME'),
        'op_admin_pass': (os.getenv('OPENSTACK_ADMIN_PASSWORD') or "").strip("'"),  # noqa

        # job & worker
        'try_period': int(os.getenv('TRY_PERIOD') or 30),
        'erase_delay': int(os.getenv('ERASE_DELAY') or 2 * 3600),

        'pick_size': int(os.getenv('WORKER_PICK_SIZE') or 10),
        'exec_size': int(os.getenv('WORKER_EXEC_SIZE') or 10),
        'exec_timeout': int(os.getenv('WORKER_EXEC_TIMEOUT') or 600),

        # billing config
        'billing_endpoint': os.getenv('BILLING_ENDPOINT'),
        'billing_debug': os.getenv('BILLING_DEBUG') == 'True',
        'billing_key': os.getenv('BILLING_KEY'),
        'billing_secret': os.getenv('BILLING_SECRET'),
        'billing_flavors': (os.getenv('BILLING_FLAVORS') or "").strip(""),

        # notify
        'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
        'notify_sms_url': os.getenv('NOTIFY_SMS_URL'),
        'notify_sms_key': os.getenv('NOTIFY_SMS_KEY'),
        'notify_sms_secret': os.getenv('NOTIFY_SMS_SECRET'),
        'notify_sms_mobiles': os.getenv('NOTIFY_SMS_MOBILE'),
    }

    # set app name, require region be
    assert bool(settings['region']), 'must set REGION= in environment variable'
    settings['app_name'] = settings['region'] + '-icebox'

    # set app root. required.
    app_root = os.path.dirname(os.path.abspath(__file__))
    settings['app_root'] = app_root

    # set log dir. required.
    log_dir = os.getenv('LOG_DIR')
    if not log_dir:
        log_dir = os.path.abspath(os.path.join(app_root, os.pardir, "logs"))
    settings['log_dir'] = log_dir

    CONF.apply(**settings)
