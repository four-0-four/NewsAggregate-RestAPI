"""added subdivision_type to Province

Revision ID: 160a2bc5595a
Revises: c69980d5d1d5
Create Date: 2023-12-04 17:43:08.612256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '160a2bc5595a'
down_revision: Union[str, None] = 'c69980d5d1d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('provinces', sa.Column('subdivision_type', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('provinces', 'subdivision_type')
