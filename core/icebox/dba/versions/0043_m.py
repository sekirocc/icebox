"""-m

Revision ID: 3d89444b000d
Create Date: 2021-11-23 09:42:30.762837

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '3d89444b000d'
down_revision = '8aba43ee8d3'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('load_balancer_listener', column_name='balance_mode',
                    type_=sa.String(50), nullable=False)  # noqa


def downgrade():
    pass
