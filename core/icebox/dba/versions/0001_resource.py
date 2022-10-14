"""resource

Revision ID: 51b1bdc39fa2
Create Date: 2021-05-13 10:20:00.937896

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '51b1bdc39fa2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resource',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('resource_id', sa.String(32), nullable=False),
        sa.Column('resource_type', sa.String(32), nullable=False),
        sa.Column('resource_name', sa.String(50), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('resource')
