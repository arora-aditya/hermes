"""merge heads

Revision ID: b25e8e09c164
Revises: 73ca3fee495f, 8a4f2c1d3e5b
Create Date: 2025-04-13 13:21:16.626043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b25e8e09c164'
down_revision: Union[str, None] = ('73ca3fee495f', '8a4f2c1d3e5b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
