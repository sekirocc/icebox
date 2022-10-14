"""volume_desc_length

Revision ID: 3719cf217eb9
Create Date: 2021-08-09 01:48:21.855229

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '3719cf217eb9'
down_revision = '538bac81c28a'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('volume', column_name='description', type_=sa.String(250), nullable=True)  # noqa


def downgrade():
    op.alter_column('volume', column_name='description', type_=sa.String(250), nullable=True)  # noqa
