from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "20251108_pix_ledger"
down_revision = None  # ajuste se você tiver uma última revision; se tiver, coloque o id dela aqui
branch_labels = None
depends_on = None

def upgrade():
    if not op.get_bind().dialect.has_table(op.get_bind(), "pix_ledger"):
        op.create_table(
            "pix_ledger",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, nullable=False, index=True),
            sa.Column("kind", sa.String(length=6), nullable=False),
            sa.Column("amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("ref_tx_id", sa.Integer, nullable=True),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.CheckConstraint("kind in ('credit','debit')", name="ck_pix_ledger_kind"),
            sa.CheckConstraint("amount >= 0", name="ck_pix_ledger_amount_nonneg"),
        )
        op.create_index("ix_pix_ledger_user_created", "pix_ledger", ["user_id", "created_at"])

def downgrade():
    op.drop_index("ix_pix_ledger_user_created", table_name="pix_ledger")
    op.drop_table("pix_ledger")
