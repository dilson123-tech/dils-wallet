from fastapi import APIRouter, Depends, HTTPException, Header
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

router = APIRouter(prefix="/pix", tags=["pix"])

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

    # seed automático apenas para o endpoint MOCK: cria contas se não existirem
    if not a_from or not a_to:
        try:
            if not a_from:
                a_from = Account(id=body.from_account_id, owner=f"mock:{body.from_account_id}", balance=1000.0)
                db.add(a_from)
            if not a_to:
                a_to = Account(id=body.to_account_id, owner=f"mock:{body.to_account_id}", balance=100.0)
                db.add(a_to)
            db.flush()  # garante IDs agora
        except IntegrityError:
            db.rollback()
            # corrida? reconsulta após rollback
            a_from = db.get(Account, body.from_account_id)
            a_to   = db.get(Account, body.to_account_id)

        if not a_from or not a_to:
            raise HTTPException(404, "Conta inexistente")

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
