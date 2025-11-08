from sqlalchemy import text
from app.database import engine

DDL = """
INSERT INTO pix_ledger (user_id, kind, amount, ref_tx_id, description, created_at)
SELECT u.id, 'credit', u.saldo, NULL, 'seed saldo inicial', CURRENT_TIMESTAMP
FROM user_main u
WHERE u.saldo IS NOT NULL
  AND u.saldo > 0
  AND NOT EXISTS (
    SELECT 1 FROM pix_ledger l WHERE l.user_id = u.id
  );
"""

def seed_ledger_from_users():
    with engine.begin() as conn:
        conn.execute(text(DDL))
