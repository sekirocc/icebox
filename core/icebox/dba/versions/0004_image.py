"""image

Revision ID: d8cac37c455a
Create Date: 2021-05-13 10:20:13.234890

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'd8cac37c455a'
down_revision = 'f662eae6847a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'image',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('size', sa.Integer, nullable=False),
        sa.Column('platform', sa.String(15), nullable=False),
        sa.Column('os_family', sa.String(15), nullable=False),
        sa.Column('processor_type', sa.String(15), nullable=False),
        sa.Column('min_vcpus', sa.Integer, nullable=False),
        sa.Column('min_memory', sa.Integer, nullable=False),
        sa.Column('min_disk', sa.Integer, nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('op_image_id', sa.String(36), nullable=False, index=True, unique=True),  # noqa

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('image')
