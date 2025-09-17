from alembic import op
import sqlalchemy as sa

revision = "2e7fff7cce2f"
down_revision = "7c405ce34765"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("type", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

def downgrade() -> None:
    """Downgrade schema."""
    pass

