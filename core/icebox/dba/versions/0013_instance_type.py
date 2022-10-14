"""instance_type

Revision ID: bfe737815b48
Create Date: 2021-05-20 09:44:14.790637

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'bfe737815b48'
down_revision = '9cfc07b5337c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'instance_type',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('op_flavor_id', sa.String(36), nullable=False, index=True, unique=True),  # noqa
        sa.Column('vcpus', sa.Integer, nullable=False),
        sa.Column('memory', sa.Integer, nullable=False),
        sa.Column('disk', sa.Integer, nullable=False),
        sa.Column('status', sa.String(10), nullable=False),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('instance_type')
