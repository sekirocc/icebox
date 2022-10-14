import env  # noqa
from icebox.dba import actions


class Test:

    def setup(self):
        env.create_db()

    def test_migrate(self):
        actions.migrate()

    def test_downgrade(self):
        actions.migrate()

        while actions.downgrade():
            pass

        actions.migrate()
