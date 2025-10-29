"""add_coluna_referencia_em_transactions

Revision ID: 37b4efe4ddb6
Revises: 3e0a067ec5ce
Create Date: 2025-09-15

Migration ajustada pra não quebrar se a coluna já existir.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '37b4efe4ddb6'
down_revision = 'a0e30676ce5e'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_cols = [c['name'] for c in inspector.get_columns('transactions')]

    if 'referencia' not in existing_cols:
        op.add_column(
            'transactions',
            sa.Column(
                'referencia',
                sa.String(length=64),
                nullable=True,
                server_default=''
            )
        )

def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_cols = [c['name'] for c in inspector.get_columns('transactions')]

    if 'referencia' in existing_cols:
        op.drop_column('transactions', 'referencia')
