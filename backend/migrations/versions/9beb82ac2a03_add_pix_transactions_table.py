"""add pix_transactions table

Revision ID: 9beb82ac2a03
Revises: 37b4efe4ddb6
Create Date: 2025-10-27 23:28:24.823477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9beb82ac2a03'
down_revision: Union[str, Sequence[str], None] = '37b4efe4ddb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
