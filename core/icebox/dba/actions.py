import os
import pkg_resources
import alembic
import alembic.config
from densefog import db

from alembic.script import ScriptDirectory

_old_rev_path = ScriptDirectory._rev_path


def _rev_path(self, path, rev_id, message, create_date):
    ole_path = _old_rev_path(self, path, rev_id, message, create_date)
    old_filename = os.path.basename(ole_path)

    index = old_filename.index('_')
    filename = create_date.strftime('%Y%m%d%H%M%S') + old_filename[index:]
    return os.path.join(path, filename)


ScriptDirectory._rev_path = _rev_path


def setup():
    script_location = pkg_resources.resource_filename('icebox', 'dba')

    alembic_cfg = alembic.config.Config()
    alembic_cfg.set_main_option('script_location', script_location)

    file_template = '%%(year)s%%(month)s%%(day)s%%(hour)s%%(minute)s%%(second)s_%%(slug)s'  # noqa
    alembic_cfg.set_main_option('file_template', file_template)

    if db.DB:
        alembic_cfg.set_main_option('sqlalchemy.url', db.DB.strategy)
    return alembic_cfg


def migrate():
    cfg = setup()
    alembic.command.upgrade(cfg, 'head')
    db.setup()


def downgrade():
    cfg = setup()
    alembic.command.downgrade(cfg, '-1')
    db.setup()


def revision(message):
    cfg = setup()
    alembic.command.revision(cfg, message)


def backup():
    pass
