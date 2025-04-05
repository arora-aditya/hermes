"""create_conversation_tables

Revision ID: 73ca3fee495f
Revises: 1c613f11c570
Create Date: 2025-04-05 22:30:02.045432

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "73ca3fee495f"
down_revision: Union[str, None] = "1c613f11c570"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create messages and conversation_history tables."""
    # Create messages table first
    op.create_table(
        "messages",
        sa.Column("message_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("message_id"),
    )

    # Create conversation_history table with foreign key to messages
    op.create_table(
        "conversation_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("last_message_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["last_message_id"],
            ["messages.message_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add indexes
    op.create_index(
        "ix_conversation_history_conversation_id",
        "conversation_history",
        ["conversation_id"],
        unique=True,
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    """Drop conversation_history and messages tables."""
    # Drop conversation_history first (because of foreign key)
    op.drop_table("conversation_history")
    # Then drop messages
    op.drop_table("messages")
