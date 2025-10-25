#!/bin/bash
set -e

echo "[AUREA] Boot de produção iniciando..."

# garante diretório certo
cd "$(dirname "$0")"

# exporta PYTHONPATH pro backend
export PYTHONPATH="$(pwd)"

# se PORT não existir (local dev), usa 8084
export PORT="${PORT:-8084}"

echo "[AUREA] criando/atualizando schema..."
python - <<'PY'
from decimal import Decimal
from datetime import datetime, timezone
from app.database import SessionLocal, engine
from app.models import Base, User, Transaction
from app.utils.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# garante admin
admin = db.query(User).filter_by(username="admin").first()
if not admin:
    admin = User(
        username="admin",
        hashed_password=hash_password("admin"),
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

# garante um cliente demo pra vitrine
cliente = db.query(User).filter_by(username="cliente1").first()
if not cliente:
    cliente = User(
        username="cliente1",
        hashed_password=hash_password("123456"),
        role="customer"
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    # crédito e débito iniciais, só se era novo
    txs = [
        Transaction(
            user_id=cliente.id,
            kind="credit",
            description="Depósito inicial Aurea",
            amount=Decimal("500.00"),
            created_at=datetime.now(timezone.utc),
        ),
        Transaction(
            user_id=cliente.id,
            kind="debit",
            description="Pagamento QR Code Mercado",
            amount=Decimal("75.40"),
            created_at=datetime.now(timezone.utc),
        ),
    ]
    db.add_all(txs)
    db.commit()

db.close()
print("[AUREA] schema e seed OK")
PY

echo "[AUREA] subindo uvicorn na porta $PORT..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
