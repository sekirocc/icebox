"""subnet

Revision ID: c37597c5f1c2
Create Date: 2021-05-13 10:21:22.068426

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'c37597c5f1c2'
down_revision = 'd8cac37c455a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'subnet',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('network_id', sa.String(32), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('op_subnet_id', sa.String(36), nullable=False, index=True, unique=True),  # noqa
        sa.Column('gateway_ip', sa.String(32), nullable=False),
        sa.Column('ip_start', sa.String(32), nullable=False),
        sa.Column('ip_end', sa.String(32), nullable=False),
        sa.Column('cidr', sa.String(32), nullable=False),

        sa.Column('status', sa.String(10), nullable=True),
        sa.Column('op_router_id', sa.String(36), nullable=True),
        sa.Column('op_network_id', sa.String(36), nullable=True),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('subnet')
