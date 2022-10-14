"""add resource to operation

Revision ID: 191a2c2988fe
Create Date: 2021-08-10 08:10:14.603868

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '191a2c2988fe'
down_revision = '3719cf217eb9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('operation',
                  sa.Column('resource_type', sa.String(25), nullable=False))
    op.add_column('operation',
                  sa.Column('resource_ids', sa.Text, nullable=True))


def downgrade():
    op.drop_column('operation', 'resource_type')
    op.drop_column('operation', 'resource_ids')
