from fastapi import APIRouter, Depends, HTTPException, Header
from decimal import Decimal
from datetime import datetime

def _coerce(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def _row_to_jsonable(row):
    d = dict(row._mapping)
    for k, v in list(d.items()):
        d[k] = _coerce(v)
    return d


from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from backend.app.deps import get_db, get_current_user
from backend.app.models.account import Account
from backend.app.models.pix_transaction import PixTransaction
from backend.app.models import Transaction  # usa o Transaction de backend/app/models.py
from backend.app.pix.schemas import PixMockIn, PixMockOut
from backend.app.core.crypto import stable_hash_payload
import json
import os

router = APIRouter(tags=["pix"])

@router.post("/mock-transfer", response_model=PixMockOut)
def pix_mock_transfer(
    body: PixMockIn,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    x_idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    idem = x_idempotency_key or body.idempotency_key
    if not idem:
        raise HTTPException(400, "Idempotency-Key ausente")

    req_hash = stable_hash_payload(body.model_dump())
    found = db.execute(
        text("SELECT response_body, request_hash FROM idempotency_keys WHERE key = :k"),
        {"k": idem},
    ).fetchone()
    if found:
        if found[1] != req_hash:
            raise HTTPException(409, "Idempotency-Key reuse com payload diferente")
        return json.loads(found[0])

    if body.from_account_id == body.to_account_id:
        raise HTTPException(400, "Conta de origem e destino não podem ser iguais")

    a_from = db.get(Account, body.from_account_id)
    a_to   = db.get(Account, body.to_account_id)



    # (feature-flag) seed automático controlado por env PIX_MOCK_SEED_ENABLED
    if os.getenv('PIX_MOCK_SEED_ENABLED', '').lower() in ('1','true','yes'):
        if not a_from or not a_to:
            try:
                if not a_from:
                    a_from = Account(id=body.from_account_id, owner=f'mock:{body.from_account_id}', balance=1000.0)
                    db.add(a_from)
                if not a_to:
                    a_to = Account(id=body.to_account_id, owner=f'mock:{body.to_account_id}', balance=100.0)
                    db.add(a_to)
                db.flush()
            except IntegrityError:
                db.rollback()
                a_from = db.get(Account, body.from_account_id)
                a_to   = db.get(Account, body.to_account_id)

    if not a_from or not a_to:
        raise HTTPException(404, 'Conta inexistente')

    if a_from.balance < body.amount:
        raise HTTPException(422, "Saldo insuficiente")

    try:
        # cria duas transações de acordo com teu modelo (user_id/tipo/valor/referencia)
        debit  = Transaction(user_id=a_from.id, tipo="PIX_MOCK_DEBIT",  valor=float(body.amount), referencia=f"to:{a_to.id}")
        credit = Transaction(user_id=a_to.id,   tipo="PIX_MOCK_CREDIT", valor=float(body.amount), referencia=f"from:{a_from.id}")
        db.add_all([debit, credit])

        # aplica saldos
        a_from.balance -= body.amount
        a_to.balance   += body.amount

        db.flush()  # gera IDs nas transações

        resp = PixMockOut(
            status="ok",
            debit_tx_id=debit.id,
            credit_tx_id=credit.id,
            balance_from=float(a_from.balance),
            balance_to=float(a_to.balance),
        )
        # persiste idempotência via SQL textual (agora com text())
        db.execute(
            text("INSERT INTO idempotency_keys (key, request_hash, response_body) VALUES (:k, :h, :b)"),
            {"k": idem, "h": req_hash, "b": json.dumps(resp.model_dump())},
        )

        # --- loga histórico PIX (mock) junto na mesma transação ---
        try:
            rec = PixTransaction(
                from_account_id=body.from_account_id,
                to_account_id=body.to_account_id,
                amount=float(body.amount),
            )
            db.add(rec)
        except Exception as _e:
            # não quebra o fluxo do PIX mock; apenas segue sem histórico
            pass

        db.commit()
        return resp
    except:
        db.rollback()
        raise

from decimal import Decimal
from datetime import datetime

# --- helpers de serialização seguros ---
def _coerce(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def _row_to_jsonable(row):
    # suporta RowMapping (.mappings()) e Row via ._mapping
    if hasattr(row, "items"):
        d = dict(row)
    else:
        d = dict(row._mapping)
    for k, v in list(d.items()):
        d[k] = _coerce(v)
    return d

# --- /summary: por conta (usa pix_transactions) ---
@router.get("/summary", summary="Resumo PIX por conta")
def pix_summary():
    from backend.app.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        q = db.execute(text("""
            WITH t AS (
                SELECT to_account_id    AS account_id,
                       amount           AS received,
                       0::numeric       AS sent
                FROM pix_transactions
                UNION ALL
                SELECT from_account_id  AS account_id,
                       0::numeric       AS received,
                       amount           AS sent
                FROM pix_transactions
            )
            SELECT account_id,
                   SUM(received)            AS total_received,
                   SUM(sent)                AS total_sent,
                   SUM(received - sent)     AS net_balance
            FROM t
            GROUP BY account_id
            ORDER BY account_id
        """))
        rows = q.mappings().all() if hasattr(q, "mappings") else q.fetchall()
        return [_row_to_jsonable(r) for r in rows]
    finally:
        db.close()

# --- /stats: agregados globais (usa pix_transactions) ---
@router.get("/stats", summary="Estatisticas gerais de transacoes PIX")
def pix_stats():
    from backend.app.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        q = db.execute(text("""
            SELECT COUNT(*)        AS total_count,
                   SUM(amount)     AS total_amount,
                   AVG(amount)     AS avg_amount,
                   MIN(amount)     AS min_amount,
                   MAX(amount)     AS max_amount,
                   MAX(created_at) AS last_tx
            FROM pix_transactions
        """))
        row = q.mappings().one() if hasattr(q, "mappings") else q.fetchone()
        return _row_to_jsonable(row)
    finally:
        db.close()
