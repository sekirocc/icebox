"""add connection_limit to table load_balancer_listener

Revision ID: 8aba43ee8d3
Create Date: 2021-10-13 06:24:06.820948

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '8aba43ee8d3'
down_revision = '336bc285497c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('load_balancer_listener', sa.Column('connection_limit', sa.Integer, nullable=True))   # noqa


def downgrade():
    op.drop_column('load_balancer_listener', 'connection_limit')
