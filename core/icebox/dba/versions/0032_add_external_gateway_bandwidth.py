"""add external gateway bandwidth


Revision ID: 2a007684119c
Create Date: 2021-08-17 06:02:33.257718

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '2a007684119c'
down_revision = '191a2c2988fe'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('network',
                  sa.Column('external_gateway_bandwidth', sa.Integer, nullable=False))   # noqa


def downgrade():
    op.drop_column('network', 'external_gateway_bandwidth')
