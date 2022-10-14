"""network

Revision ID: 688b35b88ea9
Create Date: 2021-05-13 10:21:26.441125

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '688b35b88ea9'
down_revision = 'c37597c5f1c2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'network',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('op_router_id', sa.String(36), nullable=False, index=True, unique=True),  # noqa
        sa.Column('op_network_id', sa.String(36), nullable=False, index=True, unique=True),  # noqa

        sa.Column('external_gateway_ip', sa.String(15), nullable=True),

        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('network')
