"""add deleted ceased time to resources

Revision ID: a2dc9403a8ab
Create Date: 2021-07-05 02:14:51.469662

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'a2dc9403a8ab'
down_revision = '32a2ae335370'
branch_labels = None
depends_on = None

resources = ['instance', 'instance_type', 'key_pair',
             'eip', 'network', 'subnet', 'port_forwarding',
             'image', 'volume', 'snapshot']


def upgrade():
    for resource in resources:
        op.add_column(resource, sa.Column('deleted', sa.DateTime(), nullable=True))      # noqa
        op.add_column(resource, sa.Column('ceased', sa.DateTime(), nullable=True))      # noqa


def downgrade():
    for resource in resources:
        op.drop_column(resource, 'deleted')
        op.drop_column(resource, 'ceased')
