"""add volume type to snapshot

Revision ID: 566e68d75489
Create Date: 2021-07-15 08:26:09.391620

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '566e68d75489'
down_revision = '99eeccd66317'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('snapshot',
                  sa.Column('volume_type', sa.String(32), nullable=False))
    op.execute(
        sa.sql.table('snapshot',
                     sa.sql.column('volume_type'))
          .update()
          .values({
              'volume_type': op.inline_literal('normal'),
          })
    )


def downgrade():
    op.drop_column('snapshot', 'volume_type')
