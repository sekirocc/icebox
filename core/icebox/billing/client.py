import traceback
import json

from icebox.billing import instances
from icebox.billing import eips
from icebox.billing import volumes
from icebox import config

from densefog.common import request

from densefog import logger
logger = logger.getChild(__file__)


class Client(object):
    def __init__(self):
        self.region = config.CONF.region

        self.instances = instances.InstanceBiller(self)
        self.eips = eips.EipBiller(self)
        self.volumes = volumes.VolumeBiller(self)

        self.billing_endpoint = config.CONF.billing_endpoint
        self.billing_key = config.CONF.billing_key
        self.billing_secret = config.CONF.billing_secret

        self.headers = {
            'X-Ice-Key': self.billing_key,
            'X-Ice-Secret': self.billing_secret,
        }

    def post(self, body):
        logger.debug('client.post, body: %s' % body)

        resp = None
        try:
            assert bool(self.billing_endpoint), 'did not set billing endpoint'
            assert bool(self.billing_key), 'did not set billing key'
            assert bool(self.billing_secret), 'did not set billing secret'

            result = request.post(self.billing_endpoint,
                                  json.dumps(body),
                                  self.headers,
                                  logger)

            resp = json.loads(result)
            assert resp['retCode'] == 0, 'billing service reCode is not 0!'

            return resp

        except Exception:
            stack = traceback.format_exc()
            logger.trace(stack)
            logger.error("request url: \n%s" % self.billing_endpoint)
            logger.error("request header: \n%s" % self.headers)
            logger.error("request body: \n%s" % json.dumps(body, indent=2))
            logger.error("response: \n%s" % json.dumps(resp, indent=2))

    def get(self):
        logger.debug('client.get')

        pass


client = Client()
