"""changed newscorporation

Revision ID: f82d7bbb5ebf
Revises: 686627043b70
Create Date: 2023-12-27 08:22:35.491321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'f82d7bbb5ebf'
down_revision: Union[str, None] = '686627043b70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('newsCorporations', sa.Column('name', sa.String(length=100), nullable=True))
    op.add_column('newsCorporations', sa.Column('parent', sa.String(length=100), nullable=True))
    op.add_column('newsCorporations', sa.Column('url', sa.String(length=300), nullable=True))
    op.add_column('newsCorporations', sa.Column('icon', sa.String(length=300), nullable=True))
    op.add_column('newsCorporations', sa.Column('language', sa.String(length=100), nullable=True))
    op.add_column('newsCorporations', sa.Column('location', sa.String(length=100), nullable=True))
    op.drop_column('newsCorporations', 'fullName')
    op.drop_column('newsCorporations', 'yearFounded')
    op.drop_column('newsCorporations', 'country')
    op.drop_column('newsCorporations', 'shortName')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('newsCorporations', sa.Column('shortName', mysql.VARCHAR(length=100), nullable=True))
    op.add_column('newsCorporations', sa.Column('country', mysql.VARCHAR(length=100), nullable=True))
    op.add_column('newsCorporations', sa.Column('yearFounded', mysql.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('newsCorporations', sa.Column('fullName', mysql.VARCHAR(length=100), nullable=True))
    op.drop_column('newsCorporations', 'location')
    op.drop_column('newsCorporations', 'language')
    op.drop_column('newsCorporations', 'icon')
    op.drop_column('newsCorporations', 'url')
    op.drop_column('newsCorporations', 'parent')
    op.drop_column('newsCorporations', 'name')
    # ### end Alembic commands ###