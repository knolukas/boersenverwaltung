"""Transactions und Offer erstellt

Revision ID: 72906955a73b
Revises: 0a48e6c11388
Create Date: 2023-04-23 19:20:41.198801

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72906955a73b'
down_revision = '0a48e6c11388'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('offer',
    sa.Column('security_id', sa.Integer(), nullable=False),
    sa.Column('market_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('security_id', 'market_id')
    )
    op.create_table('transactions',
    sa.Column('transaction_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('security_id', sa.Integer(), nullable=False),
    sa.Column('security_price', sa.Float(), nullable=False),
    sa.Column('security_amount', sa.Integer(), nullable=False),
    sa.Column('transaction_type', sa.Text(), nullable=False),
    sa.Column('market_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['market_id'], ['market.market_id'], ),
    sa.PrimaryKeyConstraint('transaction_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transactions')
    op.drop_table('offer')
    # ### end Alembic commands ###
