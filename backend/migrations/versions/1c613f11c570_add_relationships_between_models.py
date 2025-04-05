"""Add relationships between models

Revision ID: 1c613f11c570
Revises: 082d6354a219
Create Date: 2025-03-30 18:42:40.313559

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1c613f11c570"
down_revision: Union[str, None] = "082d6354a219"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add relationships between models."""
    # Add email column to users table with a default value
    op.add_column("users", sa.Column("email", sa.String(), nullable=True))

    # Update existing rows with a default email based on first_name and last_name
    op.execute(
        """
        UPDATE users 
        SET email = LOWER(first_name || '.' || last_name || '@example.com')
        WHERE email IS NULL
    """
    )

    # Now make the column non-nullable
    op.alter_column("users", "email", existing_type=sa.String(), nullable=False)

    # Add indexes
    op.create_index("ix_documents_filename", "documents", ["filename"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=True)


def downgrade() -> None:
    """Remove relationships between models."""
    # Drop indexes
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_documents_filename", table_name="documents")

    # Drop email column
    op.drop_column("users", "email")
