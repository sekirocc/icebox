"""load_balancer

Revision ID: 2a0cd0c49cd5
Create Date: 2021-08-31 08:54:02.817931

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '2a0cd0c49cd5'
down_revision = '5a69bf75cba2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'load_balancer',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=True),
        sa.Column('subnet_id', sa.String(32), nullable=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('bandwidth', sa.Integer, nullable=False),
        sa.Column('address', sa.String(15), nullable=False),

        sa.Column('op_floatingip_id', sa.String(36), nullable=True),
        sa.Column('op_loadbalancer_id', sa.String(36), nullable=True),

        sa.Column('status', sa.String(10), nullable=True),

        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('ceased', sa.DateTime(), nullable=True),

        mysql_DEFAULT_CHARSET='utf8'
    )

    op.create_table(
        'load_balancer_listener',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=True),
        sa.Column('load_balancer_id', sa.String(32), nullable=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),

        sa.Column('protocol', sa.String(5), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('balance_mode', sa.String(20), nullable=False),
        sa.Column('sp_mode', sa.String(7), nullable=True),
        sa.Column('sp_timeout', sa.Integer, nullable=True),
        sa.Column('sp_key', sa.String(100), nullable=True),

        sa.Column('hm_delay', sa.Integer, nullable=True),
        sa.Column('hm_timeout', sa.Integer, nullable=True),
        sa.Column('hm_expected_codes', sa.Text, nullable=True),
        sa.Column('hm_max_retries', sa.Integer, nullable=True),
        sa.Column('hm_http_method', sa.String(10), nullable=True),
        sa.Column('hm_url_path', sa.String(256), nullable=True),
        sa.Column('hm_type', sa.String(5), nullable=True),

        sa.Column('op_listener_id', sa.String(36), nullable=True),
        sa.Column('op_pool_id', sa.String(36), nullable=True),
        sa.Column('op_healthmonitor_id', sa.String(36), nullable=True),

        sa.Column('status', sa.String(10), nullable=True),

        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('deleted', sa.DateTime(), nullable=True),

        mysql_DEFAULT_CHARSET='utf8'
    )

    op.create_table(
        'load_balancer_backend',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=True),
        sa.Column('load_balancer_id', sa.String(32), nullable=True),
        sa.Column('load_balancer_listener_id', sa.String(32), nullable=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),

        sa.Column('address', sa.String(15), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),

        sa.Column('op_member_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(10), nullable=True),

        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('deleted', sa.DateTime(), nullable=True),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('load_balancer')
    op.drop_table('load_balancer_listener')
    op.drop_table('load_balancer_backend')
