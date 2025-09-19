from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '37b4efe4ddb6'
down_revision = 'a0e30676ce5e'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('transactions', sa.Column('referencia', sa.String(length=64), nullable=True, server_default=''))

def downgrade():
    op.drop_column('transactions', 'referencia')
