"""eip resource

Revision ID: b873257c244f
Create Date: 2021-06-16 12:18:07.829256

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'b873257c244f'
down_revision = '381fc39adeb6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'eip_resource',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('eip_id', sa.String(32), nullable=True),
        sa.Column('resource_id', sa.String(32), nullable=False),
        sa.Column('resource_type', sa.String(16), nullable=False),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        sa.Index('eip_id', 'eip_id'),
        sa.Index('resource_id', 'resource_id'),
        sa.Index('eip_resource', 'eip_id', 'resource_id'),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('eip_resource')
