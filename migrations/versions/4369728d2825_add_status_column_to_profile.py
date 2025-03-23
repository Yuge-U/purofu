"""Add status column to Profile

Revision ID: 4369728d2825
Revises: 81497e691622
Create Date: 2025-03-23 22:15:40.941881

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4369728d2825'
down_revision = '81497e691622'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('profile', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=10), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('profile', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
