from sqlalchemy import text
from app.database import engine

DDL = """
CREATE TABLE IF NOT EXISTS pix_ledger (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  kind VARCHAR(6) NOT NULL CHECK (kind IN ('credit','debit')),
  amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
  ref_tx_id INTEGER NULL,
  description VARCHAR(255) NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_pix_ledger_user_created ON pix_ledger(user_id, created_at);
"""

def ensure_pix_ledger():
    with engine.begin() as conn:
        conn.execute(text(DDL))
