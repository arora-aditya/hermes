"""add_document_folder_structure

Revision ID: aaa9250ae4e9
Revises: 73ca3fee495f
Create Date: 2025-04-06 23:49:41.073247

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aaa9250ae4e9"
down_revision: Union[str, None] = "73ca3fee495f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add document folder structure columns."""
    # Add new columns
    op.add_column("documents", sa.Column("full_path", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("is_folder", sa.Boolean(), server_default="false", nullable=False),
    )

    # Add foreign key constraint for parent_id
    op.create_foreign_key(
        "fk_documents_parent_id",
        "documents",
        "documents",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create index on full_path for faster lookups
    op.create_index("ix_documents_full_path", "documents", ["full_path"])

    # Create index on parent_id for faster tree traversal
    op.create_index("ix_documents_parent_id", "documents", ["parent_id"])

    # Update existing documents to have root-level full_path
    op.execute(
        """
        UPDATE documents 
        SET full_path = '/' || filename 
        WHERE full_path IS NULL
    """
    )

    # Make full_path non-nullable after setting default values
    op.alter_column("documents", "full_path", nullable=False)


def downgrade() -> None:
    """Remove document folder structure columns."""
    # Drop indexes first
    op.drop_index("ix_documents_full_path")
    op.drop_index("ix_documents_parent_id")

    # Drop foreign key constraint
    op.drop_constraint("fk_documents_parent_id", "documents", type_="foreignkey")

    # Drop columns
    op.drop_column("documents", "is_folder")
    op.drop_column("documents", "parent_id")
    op.drop_column("documents", "full_path")
