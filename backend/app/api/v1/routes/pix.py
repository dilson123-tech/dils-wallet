from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ...deps import get_db, get_current_user
from ....models.account import Account
from ....models.transaction import Transaction
from ....models.idempotency import IdempotencyKey
from ....schemas.pix import PixMockIn, PixMockOut
from ....core.crypto import stable_hash_payload
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
    found = db.get(IdempotencyKey, idem)
    if found:
        if found.request_hash != req_hash:
            raise HTTPException(409, "Idempotency-Key reuse com payload diferente")
        return json.loads(found.response_body)

    if body.from_account_id == body.to_account_id:
        raise HTTPException(400, "Conta de origem e destino não podem ser iguais")

    a_from = db.get(Account, body.from_account_id)
    a_to   = db.get(Account, body.to_account_id)
    if not a_from or not a_to:
        raise HTTPException(404, "Conta inexistente")

    if a_from.balance < body.amount:
        raise HTTPException(422, "Saldo insuficiente")

    try:
        debit = Transaction(account_id=a_from.id, amount=-body.amount, kind="PIX_MOCK_DEBIT")
        credit= Transaction(account_id=a_to.id,   amount= body.amount, kind="PIX_MOCK_CREDIT")
        db.add_all([debit, credit])

        a_from.balance -= body.amount
        a_to.balance   += body.amount

        db.flush()

        resp = PixMockOut(
            status="ok",
            debit_tx_id=debit.id,
            credit_tx_id=credit.id,
            balance_from=float(a_from.balance),
            balance_to=float(a_to.balance),
        )
        db.add(IdempotencyKey(key=idem, request_hash=req_hash, response_body=json.dumps(resp.model_dump())))
        db.commit()
        return resp
    except:
        db.rollback()
        raise
