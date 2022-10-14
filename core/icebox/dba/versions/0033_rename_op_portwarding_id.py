"""rename op_portwarding_id

Revision ID: 2e767bdfcb82
Create Date: 2021-08-22 11:14:06.400037

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '2e767bdfcb82'
down_revision = '2a007684119c'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('port_forwarding', 'op_portforwarding_id',
                    new_column_name='op_port_forwarding_id',
                    type_=sa.String(36),
                    nullable=True)


def downgrade():
    op.alter_column('port_forwarding', 'op_port_forwarding_id',
                    new_column_name='op_portforwarding_id',
                    type_=sa.String(36),
                    nullable=True)
