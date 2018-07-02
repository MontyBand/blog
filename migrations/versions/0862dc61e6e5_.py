"""empty message

Revision ID: 0862dc61e6e5
Revises: 603c2081bbd9
Create Date: 2018-06-25 14:11:21.155653

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0862dc61e6e5'
down_revision = '603c2081bbd9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('articles', sa.Column('portada', sa.String(length=500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('articles', 'portada')
    # ### end Alembic commands ###