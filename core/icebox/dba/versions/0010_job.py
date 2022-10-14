"""job

Revision ID: f60452e2e987
Create Date: 2021-05-15 14:38:33.477165

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'f60452e2e987'
down_revision = 'd147ae0715e4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'job',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('error', sa.Text, nullable=False),
        sa.Column('result', sa.Text, nullable=False),
        sa.Column('params', sa.Text, nullable=False),

        sa.Column('run_at', sa.DateTime(), nullable=False),
        sa.Column('try_period', sa.Integer, nullable=False),
        sa.Column('try_max', sa.Integer, nullable=False),
        sa.Column('trys', sa.Integer, nullable=False),
        sa.Column('project_id', sa.String(32), nullable=True),

        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        mysql_DEFAULT_CHARSET='utf8'
    )


def downgrade():
    op.drop_table('job')
