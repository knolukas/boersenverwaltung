"""user update

Revision ID: 0a48e6c11388
Revises: b377b567ef03
Create Date: 2023-04-23 18:56:53.808470

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a48e6c11388'
down_revision = 'b377b567ef03'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('about_me')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('about_me', sa.VARCHAR(length=140), nullable=True))

    # ### end Alembic commands ###