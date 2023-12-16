"""renaming some of the columns of user

Revision ID: 763c09cbee93
Revises: 25ef505e54f7
Create Date: 2023-12-13 07:46:56.122266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '763c09cbee93'
down_revision: Union[str, None] = '25ef505e54f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False))
    op.add_column('users', sa.Column('hashed_password', sa.String(length=300), nullable=False))
    op.alter_column('users', 'profile_picture_id',
               existing_type=mysql.INTEGER(),
               nullable=True)
    op.drop_column('users', 'password')
    op.drop_column('users', 'is_internal')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_internal', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('password', mysql.VARCHAR(length=300), nullable=False))
    op.alter_column('users', 'profile_picture_id',
               existing_type=mysql.INTEGER(),
               nullable=False)
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'is_active')
    # ### end Alembic commands ###