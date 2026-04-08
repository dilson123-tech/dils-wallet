"""align users schema with auth model

Revision ID: c9f4a1b2d3e4
Revises: 708c9f277a27
Create Date: 2026-04-08 08:25:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9f4a1b2d3e4"
down_revision: Union[str, Sequence[str], None] = "708c9f277a27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if "users" not in insp.get_table_names():
        return

    cols = {c["name"]: c for c in insp.get_columns("users")}

    if "full_name" not in cols:
        op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))

    if "password_hash" not in cols:
        op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))

    if "type" not in cols:
        op.add_column("users", sa.Column("type", sa.String(length=20), nullable=True))

    cols = {c["name"]: c for c in sa.inspect(bind).get_columns("users")}

    if "hashed_password" in cols and "password_hash" in cols:
        op.execute(
            sa.text(
                """
                UPDATE users
                   SET password_hash = hashed_password
                 WHERE (password_hash IS NULL OR password_hash = '')
                   AND hashed_password IS NOT NULL
                """
            )
        )

    if "role" in cols and "type" in cols:
        op.execute(
            sa.text(
                """
                UPDATE users
                   SET type = role
                 WHERE (type IS NULL OR type = '')
                   AND role IS NOT NULL
                """
            )
        )

    if "username" in cols and "email" in cols:
        op.execute(
            sa.text(
                """
                UPDATE users
                   SET email = username
                 WHERE (email IS NULL OR email = '')
                   AND username IS NOT NULL
                   AND username LIKE '%@%'
                """
            )
        )

    cols = {c["name"]: c for c in sa.inspect(bind).get_columns("users")}

    if "password_hash" in cols and cols["password_hash"].get("nullable", True):
        op.alter_column(
            "users",
            "password_hash",
            existing_type=sa.String(length=255),
            nullable=False,
        )

    if "type" in cols and cols["type"].get("nullable", True):
        op.alter_column(
            "users",
            "type",
            existing_type=sa.String(length=20),
            nullable=False,
        )


def downgrade() -> None:
    pass
