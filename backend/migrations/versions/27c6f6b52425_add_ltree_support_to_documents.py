"""add_ltree_support_to_documents

Revision ID: 27c6f6b52425
Revises: b25e8e09c164
Create Date: 2025-04-13 13:22:22.522620

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "27c6f6b52425"
down_revision: Union[str, None] = "b25e8e09c164"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable required PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree;")

    # Add new column for ltree path
    op.add_column("documents", sa.Column("path_ltree", sa.String(), nullable=True))

    # Convert existing path_array data to ltree format
    # Replace special characters and join with dots
    op.execute(
        """
        UPDATE documents 
        SET path_ltree = (
            array_to_string(path_array, '.') || '.' || 
            regexp_replace(filename, '[^a-zA-Z0-9]', '_', 'g')
        )::text
        WHERE path_array IS NOT NULL
    """
    )

    # Make path_ltree not nullable after data migration
    op.alter_column(
        "documents", "path_ltree", existing_type=sa.String(), nullable=False
    )

    # Create trigram index for filename
    op.execute(
        """
        CREATE INDEX idx_document_filename_trgm 
        ON documents USING gin (filename gin_trgm_ops)
    """
    )

    # Create ltree index using raw SQL with type cast
    op.execute(
        text(
            """
        CREATE INDEX idx_document_path_ltree 
        ON documents USING gist ((path_ltree::ltree))
    """
        )
    )


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_document_filename_trgm")
    op.execute("DROP INDEX IF EXISTS idx_document_path_ltree")

    # Drop path_ltree column
    op.drop_column("documents", "path_ltree")
