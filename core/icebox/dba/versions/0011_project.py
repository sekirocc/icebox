"""project

Revision ID: 7a83343605fa
Create Date: 2021-05-19 11:24:59.309190

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '7a83343605fa'
down_revision = 'f60452e2e987'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('op_project_id', sa.String(32), nullable=False),
        sa.Column('qt_instances', sa.Integer, nullable=False),
        sa.Column('qt_vcpus', sa.Integer, nullable=False),
        sa.Column('qt_memory', sa.Integer, nullable=False),
        sa.Column('qt_images', sa.Integer, nullable=False),
        sa.Column('qt_eips', sa.Integer, nullable=False),
        sa.Column('qt_volumes', sa.Integer, nullable=False),
        sa.Column('qt_volume_size', sa.Integer, nullable=False),
        sa.Column('qt_key_pairs', sa.Integer, nullable=False),
        sa.Column('qt_snapshots', sa.Integer, nullable=False),

        sa.Column('cu_instances', sa.Integer, nullable=False),
        sa.Column('cu_vcpus', sa.Integer, nullable=False),
        sa.Column('cu_memory', sa.Integer, nullable=False),
        sa.Column('cu_images', sa.Integer, nullable=False),
        sa.Column('cu_eips', sa.Integer, nullable=False),
        sa.Column('cu_volumes', sa.Integer, nullable=False),
        sa.Column('cu_volume_size', sa.Integer, nullable=False),
        sa.Column('cu_key_pairs', sa.Integer, nullable=False),
        sa.Column('cu_snapshots', sa.Integer, nullable=False),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        sa.Column('deleted', sa.Integer, nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('project')
