"""update table load_balancer_backend

Revision ID: 4828c65e0d97
Create Date: 2021-10-10 10:27:02.777033

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '4828c65e0d97'
down_revision = '44a953511b49'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('load_balancer_backend', sa.Column('op_pool_id', sa.String(36), nullable=True))   # noqa


def downgrade():
    op.drop_column('load_balancer_backend', 'op_pool_id')
