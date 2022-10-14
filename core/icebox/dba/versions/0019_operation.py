"""operation

Revision ID: d4a7ba5574ae
Create Date: 2021-06-20 08:04:25.884167

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'd4a7ba5574ae'
down_revision = 'b873257c244f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'operation',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('project_id', sa.String(32), nullable=True),
        sa.Column('access_key', sa.String(32), nullable=True),
        sa.Column('action', sa.String(32), nullable=True),
        sa.Column('params', sa.Text, nullable=True),
        sa.Column('ret_code', sa.Integer, nullable=True),
        sa.Column('ret_message', sa.String(100), nullable=True),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),

        sa.Index('project', 'project_id'),

        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('operation')
