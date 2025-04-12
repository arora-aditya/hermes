"""add_path_array_to_documents

Revision ID: 8a4f2c1d3e5b
Revises: 1c613f11c570
Create Date: 2024-03-21 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8a4f2c1d3e5b"
down_revision: Union[str, None] = "1c613f11c570"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add path_array column to documents table."""
    op.add_column(
        "documents",
        sa.Column(
            "path_array",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    """Remove path_array column from documents table."""
    op.drop_column("documents", "path_array")
