"""delete mountpoint mode in instance volume

Revision ID: 99eeccd66317
Create Date: 2021-07-12 08:55:52.915059

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '99eeccd66317'
down_revision = 'a2dc9403a8ab'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('instance_volume', 'mountpoint')
    op.drop_column('instance_volume', 'mode')


def downgrade():
    op.add_column('instance_volume',
                  sa.Column('mountpoint', sa.String(16), nullable=True))
    op.add_column('instance_volume',
                  sa.Column('mode', sa.String(8), nullable=True))
