"""removed language from country and state type from provinces

Revision ID: a1090d9d3a45
Revises: 160a2bc5595a
Create Date: 2023-12-04 18:45:06.123400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1090d9d3a45'
down_revision: Union[str, None] = '160a2bc5595a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Connect to the current bind (engine)
    bind = op.get_bind()
    
    # Create a MetaData object and reflect tables
    meta = sa.MetaData()
    meta.reflect(bind=bind)

    # Retrieve the 'countries' table object
    countries_table = sa.Table('countries', meta)

    # Drop the foreign key constraint
    # Replace 'fk_countries_language_id' with the actual name of the constraint
    op.drop_constraint('fk_countries_language_id', 'countries', type_='foreignkey')

    # Now that the constraint is removed, drop the 'language_id' column
    op.drop_column('countries', 'language_id')

    # Similar steps for the 'provinces' table and its 'subdivision_type' column
    # (If there's a foreign key constraint associated with 'subdivision_type', it needs to be dropped first)
    op.drop_column('provinces', 'subdivision_type')


def downgrade() -> None:
    # Add the 'language_id' column back to the 'countries' table
    op.add_column('countries', sa.Column('language_id', sa.Integer))

    # Recreate the foreign key constraint for 'language_id'
    # Adjust 'referenced_table_name' and 'referenced_column_name' to match your schema
    op.create_foreign_key('fk_countries_language_id', 'countries', 'referenced_table', ['language_id'], ['id'])

    # Similar steps for the 'provinces' table and its 'subdivision_type' column
    # Add the 'subdivision_type' column back
    op.add_column('provinces', sa.Column('subdivision_type', sa.String(length=255)))

    # If there was a foreign key constraint associated with 'subdivision_type', recreate it as well
    # op.create_foreign_key('fk_provinces_subdivision_type', 'provinces', 'other_table', ['subdivision_type'], ['id'])
