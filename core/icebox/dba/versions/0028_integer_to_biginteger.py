"""integer_to_biginteger

Revision ID: 3168e6d9389a
Create Date: 2021-08-01 07:48:16.284697

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '3168e6d9389a'
down_revision = 'ff5cadd7bc52'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('image', column_name='size', type_=sa.BigInteger, nullable=False)  # noqa


def downgrade():
    op.alter_column('image', column_name='size', type_=sa.Integer, nullable=False)  # noqa
