from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Numeric

from app.database import get_db
from app.utils.users import _ensure_user_id  # garante user e retorna ID
from app.models.pix_ledger import PixLedger

router = APIRouter()

class CreditIn(BaseModel):
    email: str = Field(..., description="Email do usuário a creditar")
    valor: float = Field(..., gt=0, description="Valor do crédito")
    desc: str | None = Field(default="seed inicial", description="Descrição opcional")

@router.post("/admin/credit-ledger")
def admin_credit_ledger(payload: CreditIn, db: Session = Depends(get_db)):
    try:
        uid = _ensure_user_id(db, payload.email)
        led = PixLedger(
            user_id=uid,
            kind="credit",
            amount=float(payload.valor),
            ref_tx_id=None,
            description=payload.desc or "seed"
        )
        db.add(led)
        db.commit()

        # saldo após crédito
        saldo = db.query(
            func.coalesce(
                func.sum(
                    case(
                        (PixLedger.kind == "credit", cast(PixLedger.amount, Numeric(14,2))),
                        else_=-cast(PixLedger.amount, Numeric(14,2))
                    )
                ), 0
            )
        ).filter(PixLedger.user_id == uid).scalar() or 0
        return {"ok": True, "user_id": uid, "saldo": float(saldo)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"admin_credit_failed: {e}")
