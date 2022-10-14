"""add qt_networks to project

Revision ID: ff5cadd7bc52
Create Date: 2021-07-20 08:31:26.750292

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'ff5cadd7bc52'
down_revision = 'ae5c62ccc751'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('project',
                  sa.Column('qt_networks', sa.Integer, nullable=False))
    op.add_column('project',
                  sa.Column('cu_networks', sa.Integer, nullable=False))

    op.execute(
        sa.sql.table('project',
                     sa.sql.column('qt_networks'),
                     sa.sql.column('cu_networks'))
          .update()
          .values({
              'qt_networks': op.inline_literal(100),
              'cu_networks': op.inline_literal(0),
          })
    )


def downgrade():
    op.drop_column('project', 'qt_networks')
    op.drop_column('project', 'cu_networks')
