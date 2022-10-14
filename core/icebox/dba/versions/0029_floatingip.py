"""floatingip

Revision ID: 538bac81c28a
Create Date: 2021-08-04 08:42:52.772845

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '538bac81c28a'
down_revision = '3168e6d9389a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'floatingip',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('address', sa.String(15), nullable=True),

        sa.Column('status', sa.String(10), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('ceased', sa.DateTime(), nullable=True),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('floatingip')
