"""add request_hash to idempotency_keys

Revision ID: 15c6d437914d
Revises: 60542c908832
Create Date: 2026-03-04 20:31:18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "15c6d437914d"
down_revision: Union[str, Sequence[str], None] = "60542c908832"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "idempotency_keys",
        sa.Column("request_hash", sa.String(length=64), nullable=True),
    )
    # index ajuda replay/lookup; não precisa ser unique
    op.create_index(
        "ix_idempotency_keys_request_hash",
        "idempotency_keys",
        ["request_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_request_hash", table_name="idempotency_keys")
    op.drop_column("idempotency_keys", "request_hash")
