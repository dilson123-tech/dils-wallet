"""create reservas table

Revision ID: 12ef452d38b9
Revises: 4f477852aa4a
Create Date: 2025-12-01 02:38:16.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "12ef452d38b9"
down_revision = "4f477852aa4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Se a tabela já existe por qualquer motivo, não tenta recriar
    if "reservas" in inspector.get_table_names():
        return

    op.create_table(
        "reservas",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("cliente", sa.String(length=120), nullable=False),
        sa.Column("recurso", sa.String(length=220), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("horario", sa.String(length=50), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index("ix_reservas_id", "reservas", ["id"])
    op.create_index("ix_reservas_data", "reservas", ["data"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "reservas" not in inspector.get_table_names():
        return

    op.drop_index("ix_reservas_data", table_name="reservas")
    op.drop_index("ix_reservas_id", table_name="reservas")
    op.drop_table("reservas")
