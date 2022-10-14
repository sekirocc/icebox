"""add_project_load_balancers_quota

Revision ID: 2bb682af01d
Create Date: 2021-09-01 05:55:32.372942

"""

from alembic import op  # noqa
import sqlalchemy as sa  # noqa
import datetime  # noqa

# revision identifiers, used by Alembic.
revision = '2bb682af01d'
down_revision = '2a0cd0c49cd5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('project',
                  sa.Column('qt_load_balancers', sa.Integer, nullable=True))
    op.add_column('project',
                  sa.Column('cu_load_balancers', sa.Integer, nullable=True))
    op.execute(
        sa.sql.table(
            'project',
            sa.sql.column('qt_load_balancers'),
            sa.sql.column('cu_load_balancers'),
        )
        .update()
        .values({
            'qt_load_balancers': op.inline_literal(1),
            'cu_load_balancers': op.inline_literal(0),
        })
    )


def downgrade():
    op.drop_column('project', 'cu_load_balancers')
    op.drop_column('project', 'qt_load_balancers')
