"""empty message

Revision ID: d0695a26d06a
Revises: 2afc362f9fb7
Create Date: 2020-07-06 17:35:52.150821

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0695a26d06a'
down_revision = '2afc362f9fb7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('genres', sa.ARRAY(sa.String()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', 'genres')
    # ### end Alembic commands ###