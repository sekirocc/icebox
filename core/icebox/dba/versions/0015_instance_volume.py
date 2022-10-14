"""instance_volume

Revision ID: 381fc39adeb6
Create Date: 2021-05-30 02:40:21.098260

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '381fc39adeb6'
down_revision = 'bfe737815b48'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'instance_volume',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('instance_id', sa.String(32), nullable=False),
        sa.Column('mountpoint', sa.String(16), nullable=False),
        sa.Column('mode', sa.String(8), nullable=False),
        sa.Column('volume_id', sa.String(36), nullable=False),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        sa.Index('instance_volume_id', 'instance_id', 'volume_id'),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('instance_volume')
