"""key pair

Revision ID: d147ae0715e4
Create Date: 2021-05-13 10:24:40.777985

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'd147ae0715e4'
down_revision = 'e61b9b6bdbe0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'key_pair',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('public_key', sa.Text, nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(10), nullable=True),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('key_pair')
