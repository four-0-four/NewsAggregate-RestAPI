"""added subdivision_type to Province

Revision ID: c69980d5d1d5
Revises: 5980d4f371b3
Create Date: 2023-12-04 17:41:18.276252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c69980d5d1d5'
down_revision: Union[str, None] = '5980d4f371b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
