"""Currency Tabelle neu

Revision ID: 45381c567107
Revises: 72906955a73b
Create Date: 2023-06-05 21:52:23.097743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45381c567107'
down_revision = '72906955a73b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('currency',
    sa.Column('market_currency_id', sa.Integer(), nullable=False),
    sa.Column('market_currency_name', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('market_currency_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('currency')
    # ### end Alembic commands ###
