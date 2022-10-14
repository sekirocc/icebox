"""increase sp length to loadbalancer listener

Revision ID: 336bc285497c
Create Date: 2021-10-12 03:51:19.565410

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '336bc285497c'
down_revision = '4828c65e0d97'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('load_balancer_listener', column_name='sp_mode',
                    type_=sa.String(20), nullable=True)  # noqa
    op.alter_column('load_balancer_listener', column_name='sp_key',
                    type_=sa.String(1024), nullable=True)  # noqa


def downgrade():
    pass
