"""add subnet resource

Revision ID: 35f3a5844013
Create Date: 2017-02-17 08:47:18.934790

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '35f3a5844013'
down_revision = '121155fa61dc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'subnet_resource',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('subnet_id', sa.String(32), nullable=True),
        sa.Column('resource_id', sa.String(32), nullable=False),
        sa.Column('resource_type', sa.String(16), nullable=False),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        sa.Index('subnet_id', 'subnet_id'),
        sa.Index('resource_id', 'resource_id'),
        sa.Index('subnet_resource', 'subnet_id', 'resource_id'),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('subnet_resource')
