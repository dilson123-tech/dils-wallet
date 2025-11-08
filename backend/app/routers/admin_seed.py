from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Numeric
from app.database import get_db
from app.models.pix_ledger import PixLedger
from app.models.user_main import User

router = APIRouter()

# --- helpers locais (sem depender de app.utils.users) ---
def _get_or_create_user(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, nome=email.split("@")[0], saldo=0)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# --- modelo da requisição ---
class CreditIn(BaseModel):
    email: str = Field(..., description="Email do usuário a creditar")
    valor: float = Field(..., gt=0, description="Valor do crédito")
    desc: str | None = Field(default="seed inicial", description="Descrição opcional")

# --- rota principal ---
@router.post("/admin/credit-ledger")
def admin_credit_ledger(payload: CreditIn, db: Session = Depends(get_db)):
    try:
        user = _get_or_create_user(db, payload.email)
        led = PixLedger(
            user_id=user.id,
            kind="credit",
            amount=float(payload.valor),
            ref_tx_id=None,
            description=payload.desc or "seed"
        )
        db.add(led)
        db.commit()

        saldo = db.query(
            func.coalesce(
                func.sum(
                    case(
                        (PixLedger.kind == "credit", cast(PixLedger.amount, Numeric(14,2))),
                        else_=-cast(PixLedger.amount, Numeric(14,2))
                    )
                ), 0
            )
        ).filter(PixLedger.user_id == user.id).scalar() or 0

        return {"ok": True, "user": user.email, "saldo": float(saldo)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"admin_credit_failed: {e}")
