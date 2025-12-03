"""merge pix_ledger e pix_transactions

Revision ID: 4f477852aa4a
Revises: 20251108_pix_ledger, 9beb82ac2a03
Create Date: 2025-12-01 02:26:47.893820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f477852aa4a'
down_revision: Union[str, Sequence[str], None] = ('20251108_pix_ledger', '9beb82ac2a03')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
