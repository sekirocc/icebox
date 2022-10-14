"""add boot volume to instance

Revision ID: 121155fa61dc
Create Date: 2021-11-23 06:29:35.625613

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '121155fa61dc'
down_revision = '3d89444b000d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('instance',
                  sa.Column('op_volume_id', sa.String(36), nullable=True))


def downgrade():
    op.drop_column('instance', 'op_volume_id')
