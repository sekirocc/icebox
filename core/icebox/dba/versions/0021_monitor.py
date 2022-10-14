"""monitor

Revision ID: fb146cc9c0ed
Create Date: 2021-06-27 11:20:38.135416

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'fb146cc9c0ed'
down_revision = '336ff0978f4e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'monitor',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('resource_id', sa.String(32), nullable=False),
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('metric', sa.String(50), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('data', sa.Text, nullable=False),
        sa.Column('interval', sa.Integer, nullable=False),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('monitor')
