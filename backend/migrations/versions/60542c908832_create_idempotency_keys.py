"""create idempotency keys

Revision ID: 60542c908832
Revises: 84a7240baafd
Create Date: 2026-03-04 17:18:44.358231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "60542c908832"
down_revision: Union[str, Sequence[str], None] = "84a7240baafd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_idempotency_keys_key",
        "idempotency_keys",
        ["key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_key", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
