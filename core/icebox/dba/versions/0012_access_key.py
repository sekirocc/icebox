"""access_key

Revision ID: 9cfc07b5337c
Create Date: 2021-05-19 11:25:04.353536

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '9cfc07b5337c'
down_revision = '7a83343605fa'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'access_key',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=False, index=True),
        sa.Column('key', sa.String(20), nullable=False, index=True, unique=True),   # noqa
        sa.Column('secret', sa.String(40), nullable=False),

        sa.Column('expire_at', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        sa.Column('deleted', sa.Integer, nullable=False),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('access_key')
