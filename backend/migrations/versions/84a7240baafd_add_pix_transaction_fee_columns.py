from alembic import op
import sqlalchemy as sa

revision = "84a7240baafd"
down_revision = "12ef452d38b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NO-OP: as colunas de taxa já existem no banco que o Alembic está migrando.
    # Mantemos esta revisão apenas para alinhar o histórico.
    pass


def downgrade() -> None:
    # NO-OP: não removemos as colunas de taxa existentes.
    pass
