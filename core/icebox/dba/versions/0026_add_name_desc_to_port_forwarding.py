"""add name desc to port forwarding

Revision ID: ae5c62ccc751
Create Date: 2021-07-15 08:28:03.594032

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = 'ae5c62ccc751'
down_revision = '566e68d75489'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('port_forwarding',
                  sa.Column('name', sa.String(50), nullable=False))
    op.add_column('port_forwarding',
                  sa.Column('description', sa.String(250), nullable=False))


def downgrade():
    op.drop_column('port_forwarding', 'name')
    op.drop_column('port_forwarding', 'description')
