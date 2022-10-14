"""port_forwarding

Revision ID: 32a2ae335370
Create Date: 2021-07-05 10:14:01.668377

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '32a2ae335370'
down_revision = 'fb146cc9c0ed'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'port_forwarding',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=True),
        sa.Column('network_id', sa.String(32), nullable=True),
        sa.Column('op_portforwarding_id', sa.String(36), nullable=True),
        sa.Column('op_router_id', sa.String(36), nullable=True),
        sa.Column('protocol', sa.String(3), nullable=True),
        sa.Column('outside_port', sa.Integer, nullable=True),
        sa.Column('inside_address', sa.String(15), nullable=True),
        sa.Column('inside_port', sa.Integer, nullable=True),
        sa.Column('status', sa.String(10), nullable=True),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('port_forwarding')
