import os
from decimal import Decimal, InvalidOperation

from sqlalchemy import inspect, text
from app.database import engine

DDL_USER_MAIN = """
INSERT INTO pix_ledger (user_id, kind, amount, ref_tx_id, description, created_at)
SELECT u.id, 'credit', u.saldo, NULL, 'seed saldo inicial', CURRENT_TIMESTAMP
FROM user_main u
WHERE u.saldo IS NOT NULL
  AND u.saldo > 0
  AND NOT EXISTS (
    SELECT 1 FROM pix_ledger l WHERE l.user_id = u.id
  );
"""

DDL_ADMIN_USERS = """
INSERT INTO pix_ledger (user_id, kind, amount, ref_tx_id, description, created_at)
SELECT u.id, 'credit', :amount, NULL, :description, CURRENT_TIMESTAMP
FROM users u
WHERE u.role = 'admin'
  AND NOT EXISTS (
    SELECT 1 FROM pix_ledger l WHERE l.user_id = u.id
  );
"""

def seed_ledger_from_users():
    """Seed idempotente.
    - Se existir user_main.saldo (dev legado), usa ele.
    - Senão, em prod (users sem saldo), só faz seed do admin se SEED_ADMIN_CREDIT estiver setado (>0).
    """
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    with engine.begin() as conn:
        if "user_main" in tables:
            cols = {c.get("name") for c in insp.get_columns("user_main")}
            if "saldo" in cols:
                conn.execute(text(DDL_USER_MAIN))
                return {"mode": "user_main.saldo"}

        amount_raw = os.getenv("SEED_ADMIN_CREDIT", "").strip()
        if not amount_raw:
            raise RuntimeError("Sem user_main.saldo em produção. Para seed do admin, defina SEED_ADMIN_CREDIT (ex: 1000) temporariamente.")
        try:
            amount = Decimal(amount_raw)
        except InvalidOperation:
            raise RuntimeError("SEED_ADMIN_CREDIT inválido (use número, ex: 1000 ou 1000.50).")
        if amount <= 0:
            raise RuntimeError("SEED_ADMIN_CREDIT deve ser > 0.")

        conn.execute(
            text(DDL_ADMIN_USERS),
            {"amount": amount, "description": f"seed admin initial credit ({amount})"},
        )
        return {"mode": "users.role=admin", "amount": str(amount)}
