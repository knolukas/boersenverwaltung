"""user clean up

Revision ID: 7648d141fa30
Revises: 073e42a6662a
Create Date: 2023-06-15 10:09:55.505406

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7648d141fa30'
down_revision = '073e42a6662a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index('ix_user_email')
        batch_op.drop_column('email')
        batch_op.drop_column('last_seen')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_seen', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('email', sa.VARCHAR(length=120), nullable=True))
        batch_op.create_index('ix_user_email', ['email'], unique=False)

    # ### end Alembic commands ###