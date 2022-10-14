import functools
import time

from densefog import logger
logger = logger.getChild(__file__)

# seconds for client to expire
CACHE_CLIENT_EXPIRE_SECONDS = 60 * 30

# cache_clients is a dict. example:
# {
#     'compute':  {
#         'project_id': {
#             'client': client,
#             'expire_at': time.time()
#         }
#     }
# }
cache_clients = {}


def cache_openstack_client(resource):
    """
    decorator for trying to get openstack client from caches.
    decorated method MUST have atmost one argument: project_id

    the caches are keyed with project_id (or None if not pass in)
    the caches will expired after CACHE_CLIENT_EXPIRE_SECONDS
    this expire seconds value must be smaller than openstack token expires.
    by default openstack token expires after 1 hour. so we set half hour here.
    """
    def outer(method):
        @functools.wraps(method)
        def cache(*args, **kwargs):
            # extract project_id from arguments.
            project_id = None
            if args:
                project_id = args[0]
            if kwargs:
                project_id = kwargs.get('project_id', None)

            # try to get from cache.
            logger.debug('try get %s client from cache. project_id: %s' % (
                resource, project_id))
            try:
                cached = cache_clients[resource][project_id]
            except:
                cached = None

            # if get cache. check if expired.
            now = time.time()
            if cached and cached['expire_at'] > now:
                logger.debug('hit cache.')
                return cached['client']

            logger.debug('miss cache.')
            # if no cache found.
            c = method(*args, **kwargs)

            # set cache.
            logger.debug('set cache.')
            resource_cache = cache_clients.setdefault(resource, {})
            resource_cache[project_id] = {
                'expire_at': now + CACHE_CLIENT_EXPIRE_SECONDS,
                'client': c,
            }
            # return the client.
            return c

        return cache

    return outer
