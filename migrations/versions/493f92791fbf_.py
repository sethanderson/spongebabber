"""empty message

Revision ID: 493f92791fbf
Revises: 2f58434817b4
Create Date: 2022-07-08 22:57:02.538940

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '493f92791fbf'
down_revision = '2f58434817b4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('log_request', sa.Column('ip_address', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('log_request', 'ip_address')
    # ### end Alembic commands ###
