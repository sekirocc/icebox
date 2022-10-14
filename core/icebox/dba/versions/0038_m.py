"""-m

Revision ID: 368c945b11a0
Create Date: 2021-09-29 09:52:04.459881

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '368c945b11a0'
down_revision = '11b32c773a5e'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('operation', column_name='action',
                    type_=sa.String(50), nullable=True)  # noqa


def downgrade():
    pass
