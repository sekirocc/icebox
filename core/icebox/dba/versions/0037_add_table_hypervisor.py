"""add table hypervisor

Revision ID: 11b32c773a5e
Create Date: 2021-09-08 13:54:14.461532

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '11b32c773a5e'
down_revision = '2bb682af01d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hypervisor',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('current_workload', sa.Integer, nullable=False),
        sa.Column('disk_available_least', sa.Integer, nullable=False),
        sa.Column('free_disk_gb', sa.Integer, nullable=False),
        sa.Column('free_ram_mb', sa.Integer, nullable=False),
        sa.Column('host_ip', sa.String(15), nullable=False),
        sa.Column('hypervisor_type', sa.String(15), nullable=False),
        sa.Column('hypervisor_version', sa.String(15), nullable=False),
        sa.Column('local_gb', sa.Integer, nullable=False),
        sa.Column('local_gb_used', sa.Integer, nullable=False),
        sa.Column('memory_mb', sa.Integer, nullable=False),
        sa.Column('memory_mb_used', sa.Integer, nullable=False),
        sa.Column('running_vms', sa.Integer, nullable=False),
        sa.Column('vcpus', sa.Integer, nullable=False),
        sa.Column('vcpus_used', sa.Integer, nullable=False),

        sa.Column('op_hyper_id', sa.String(36), nullable=False, index=True, unique=True),  # noqa
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('state', sa.String(10), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('hypervisor')
