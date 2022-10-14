import sys
from densefog.server import create_api
from densefog.server import create_worker

from icebox import config


def public():
    config.setup(gevent=True)

    debug = config.CONF.debug
    api = create_api('public', debug=debug)

    from icebox.api.public import switch
    api.route(switch).start(port=config.CONF.public_port)


def manage():
    config.setup(gevent=True)

    debug = config.CONF.debug
    api = create_api('manage', debug=debug)

    from icebox.api.manage import switch
    api.route(switch).start(port=config.CONF.manage_port)


def worker():
    config.setup(gevent=True)

    pick_size = config.CONF.pick_size
    exec_size = config.CONF.exec_size
    exec_timeout = config.CONF.exec_timeout

    worker = create_worker(pick_size=pick_size,
                           exec_size=exec_size,
                           exec_timeout=exec_timeout,
                           gevent=True)

    from icebox.notify import JobFailSlackNotifier
    from icebox.notify import JobFailSMSNotifier

    notis = [JobFailSlackNotifier(), JobFailSMSNotifier()]
    worker.add_notifiers(notis).start()


def shell():
    config.setup(gevent=True)

    from densefog import bootstrap
    from densefog import logger

    bootstrap.init()
    logger.init(dirname='shell')

    from IPython import embed
    embed()


def dba():
    config.setup(gevent=True)

    from densefog import bootstrap
    from densefog import logger

    bootstrap.init()
    logger.init(dirname='dba')

    from icebox.dba import actions

    command = sys.argv[1]
    if command == 'migrate':
        actions.migrate()
    if command == 'revision':
        actions.revision(sys.argv[2])
    if command == 'downgrade':
        actions.downgrade()
    if command == 'backup':
        actions.backup()
