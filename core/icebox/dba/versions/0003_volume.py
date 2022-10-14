"""volume

Revision ID: f662eae6847a
Create Date: 2021-05-13 10:20:09.525064

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'f662eae6847a'
down_revision = 'a758b21760d0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'volume',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('op_volume_id', sa.String(36), nullable=False, index=True, unique=True),  # noqa
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(100), nullable=False),

        sa.Column('size', sa.Integer, nullable=False),
        sa.Column('volume_type', sa.String(32), nullable=False),

        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('volume')
