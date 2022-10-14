"""project deleted null

Revision ID: 5a69bf75cba2
Create Date: 2021-08-19 09:27:03.621054

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '5a69bf75cba2'
down_revision = '2e767bdfcb82'
branch_labels = None
depends_on = None


def upgrade():
    # change from Integer => Datetime.
    op.drop_column('project', 'deleted')
    op.add_column('project', sa.Column('deleted', sa.DateTime(), nullable=True))      # noqa

    op.add_column('project', sa.Column('ceased', sa.DateTime(), nullable=True))      # noqa


def downgrade():
    # change from DateTime => Integer.
    op.drop_column('project', 'deleted')
    op.add_column('project', sa.Column('deleted', sa.Integer(), nullable=False))      # noqa

    op.drop_column('project', 'ceased')
