"""merge heads

Revision ID: f36d189f393f
Revises: 4e33cf223835, 7f566e777933
Create Date: 2026-04-01 12:29:25.490224

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f36d189f393f'
down_revision: Union[str, Sequence[str], None] = ('a8f3b1c2d4e5', '7f566e777933')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
