"""eip

Revision ID: b4d0081f26ac
Create Date: 2021-05-13 10:21:30.571504

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'b4d0081f26ac'
down_revision = '688b35b88ea9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'eip',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('bandwidth', sa.Integer, nullable=False),
        sa.Column('address', sa.String(15), nullable=False),

        sa.Column('resource_type', sa.String(10), nullable=True),
        sa.Column('op_floatingip_id', sa.String(36), nullable=True),

        sa.Column('status', sa.String(10), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('eip')
