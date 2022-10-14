"""add deleted ceased time to resources

Revision ID: 44a953511b49
Create Date: 2021-10-09 02:35:36.035848

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '44a953511b49'
down_revision = '368c945b11a0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('load_balancer_listener', sa.Column('ceased', sa.DateTime(), nullable=True))  # noqa
    op.add_column('load_balancer_backend', sa.Column('ceased', sa.DateTime(), nullable=True))   # noqa


def downgrade():
    op.drop_column('load_balancer_listener', 'ceased')
    op.drop_column('load_balancer_backend', 'ceased')
