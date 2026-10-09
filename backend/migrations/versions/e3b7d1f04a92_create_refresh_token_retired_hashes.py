"""create refresh_token_retired_hashes

Revision ID: e3b7d1f04a92
Revises: 77ac52cd2468
Create Date: 2026-10-09

F8.1 — reuse detection de refresh token. Guarda só o sha256 de refresh
tokens já rotacionados, ligado à família (refresh_tokens.id). Nunca o
token cru. Tabela nova e independente; não altera refresh_tokens.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3b7d1f04a92"
down_revision: Union[str, Sequence[str], None] = "77ac52cd2468"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_token_retired_hashes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "family_id",
            sa.Integer(),
            sa.ForeignKey("refresh_tokens.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_refresh_token_retired_hashes_token_hash",
        "refresh_token_retired_hashes",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_refresh_token_retired_hashes_family_id",
        "refresh_token_retired_hashes",
        ["family_id"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_token_retired_hashes_retired_at",
        "refresh_token_retired_hashes",
        ["retired_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_token_retired_hashes_retired_at", table_name="refresh_token_retired_hashes")
    op.drop_index("ix_refresh_token_retired_hashes_family_id", table_name="refresh_token_retired_hashes")
    op.drop_index("ix_refresh_token_retired_hashes_token_hash", table_name="refresh_token_retired_hashes")
    op.drop_table("refresh_token_retired_hashes")
