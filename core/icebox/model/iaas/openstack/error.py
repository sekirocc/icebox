

class OpenstackPublicNetworkNotFoundError(Exception):
    pass


def is_notfound(ex):
    return ex.__class__.__name__.find('NotFound') != -1


def is_overlimit(ex):
    return ex.__class__.__name__.find('OverLimit') != -1
