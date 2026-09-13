"""create pix_send_intents

Revision ID: 77ac52cd2468
Revises: c9f4a1b2d3e4
Create Date: 2026-09-12

M2 — autoridade server-side da intenção de envio PIX (sobrevive a
reload/fechar app/outro dispositivo/outra aba). Não substitui nem altera
`idempotency_keys` — é uma tabela nova e independente.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "77ac52cd2468"
down_revision: Union[str, Sequence[str], None] = "c9f4a1b2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pix_send_intents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("fingerprint_hash", sa.String(length=64), nullable=False),
        sa.Column("send_key", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("generation", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state in ('pending', 'acknowledged')",
            name="ck_pix_send_intents_state",
        ),
    )
    op.create_index(
        "ix_pix_send_intents_user_id",
        "pix_send_intents",
        ["user_id"],
    )
    op.create_index(
        "uq_pix_send_intents_user_fingerprint",
        "pix_send_intents",
        ["user_id", "fingerprint_hash"],
        unique=True,
    )
    op.create_index(
        "ix_pix_send_intents_send_key",
        "pix_send_intents",
        ["send_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_pix_send_intents_send_key", table_name="pix_send_intents")
    op.drop_index("uq_pix_send_intents_user_fingerprint", table_name="pix_send_intents")
    op.drop_index("ix_pix_send_intents_user_id", table_name="pix_send_intents")
    op.drop_table("pix_send_intents")
