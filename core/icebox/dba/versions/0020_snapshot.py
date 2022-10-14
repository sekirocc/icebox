"""snapshot

Revision ID: 336ff0978f4e
Create Date: 2021-06-22 06:59:35.983862

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '336ff0978f4e'
down_revision = 'd4a7ba5574ae'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'snapshot',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('op_snapshot_id', sa.String(36), nullable=True),
        sa.Column('project_id', sa.String(32), nullable=True),
        sa.Column('name', sa.String(50), nullable=True),
        sa.Column('description', sa.String(250), nullable=True),
        sa.Column('size', sa.Integer, nullable=True),
        sa.Column('status', sa.String(10), nullable=True),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('snapshot')
