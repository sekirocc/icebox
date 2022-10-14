"""instance

Revision ID: a758b21760d0
Create Date: 2021-05-13 10:20:05.764241

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'a758b21760d0'
down_revision = '51b1bdc39fa2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'instance',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('instance_type_id', sa.String(32), nullable=False),
        sa.Column('image_id', sa.String(32), nullable=False),
        sa.Column('current_vcpus', sa.Integer, nullable=False),
        sa.Column('current_memory', sa.Integer, nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('op_server_id', sa.String(36), nullable=False, index=True, unique=True),  # noqa

        sa.Column('current_disk', sa.Integer, nullable=False),
        sa.Column('op_network_id', sa.String(36), nullable=True),
        sa.Column('op_subnet_id', sa.String(36), nullable=True),
        sa.Column('op_port_id', sa.String(36), nullable=True),
        sa.Column('address', sa.String(15), nullable=True),
        sa.Column('network_id', sa.String(32), nullable=True),
        sa.Column('subnet_id', sa.String(32), nullable=True),
        sa.Column('key_pair_id', sa.String(32), nullable=True),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('instance')
