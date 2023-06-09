"""neue id spalte bei offer

Revision ID: c42bdbc1252d
Revises: c88a748c3ee4
Create Date: 2023-06-09 16:33:22.273843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c42bdbc1252d'
down_revision = 'c88a748c3ee4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_offer')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('_alembic_tmp_offer',
    sa.Column('security_id', sa.INTEGER(), nullable=False),
    sa.Column('market_id', sa.INTEGER(), nullable=False),
    sa.Column('amount', sa.INTEGER(), nullable=False),
    sa.Column('offer_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['market_id'], ['market.market_id'], name='fk_offer_market_id'),
    sa.PrimaryKeyConstraint('security_id', 'market_id')
    )
    # ### end Alembic commands ###
