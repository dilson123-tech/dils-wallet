from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import func, case

from app import database
from app.security import get_current_user
from app.models.transaction import Transaction as TxModel  # <- usa o model certo!

def _tx_to_dict(t):
    d = {
        "id": getattr(t, "id", None),
        "user_id": getattr(t, "user_id", None),
        "tipo": getattr(t, "tipo", None),
        "valor": float(getattr(t, "valor", 0) or 0),
        "descricao": None,  # coluna não existe nesse schema local
        "referencia": getattr(t, "referencia", None),
        "created_at": getattr(t, "created_at", None) or getattr(t, "criado_em", None) or datetime.utcnow(),
    }
    if hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d

class TransactionCreate(BaseModel):
    tipo: str
    valor: Union[float, str]
    descricao: Optional[str] = None
    referencia: Optional[str] = None

class BalanceOut(BaseModel):
    saldo: float

router = APIRouter(tags=["transactions"])
ALLOWED_TYPES = {"deposito", "saque", "transferencia"}

@router.post("")
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user),
):
    t = (payload.tipo or "").strip().lower()
    if t not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"tipo inválido. Use: {sorted(ALLOWED_TYPES)}")
    try:
        v = float(payload.valor)
    except Exception:
        raise HTTPException(status_code=400, detail="valor inválido")
    if v <= 0:
        raise HTTPException(status_code=400, detail="valor deve ser > 0")
    # anti-fraude: bloqueia saque > saldo
    if t == "saque":
        from sqlalchemy import func, case
        saldo_q = db.query(
            func.coalesce(
                func.sum(
                    case(
                        (models.Transaction.tipo == "deposito", models.Transaction.valor),
                        (models.Transaction.tipo == "saque", -models.Transaction.valor),
                        (models.Transaction.tipo == "transferencia", -models.Transaction.valor),
                        else_=0.0,
                    )
                ),
                0.0,
            )
        ).filter(models.Transaction.user_id == current_user.id)
        saldo_atual = float(saldo_q.scalar() or 0.0)
        if v > saldo_atual:
            raise HTTPException(status_code=400, detail="Saldo insuficiente")

    tx = TxModel(
        user_id=getattr(current_user, "id", 1),
        tipo=t,
        valor=v,
        referencia=(getattr(payload, "referencia", None) or "").strip() if getattr(payload, "referencia", None) else None,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    d = _tx_to_dict(tx)
    # reforça retorno para UX (se referencia vier None mas payload tinha valor)
    if not d.get("referencia") and getattr(payload, "referencia", None):
        d["referencia"] = getattr(payload, "referencia", None)
    if payload.descricao:
        d["descricao"] = payload.descricao
    return d

@router.get("/balance", response_model=BalanceOut)
def get_balance(
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user),
):
    total = db.query(
        func.coalesce(
            func.sum(
                case(
                    (TxModel.tipo == "deposito", TxModel.valor),
                    else_=-TxModel.valor,
                )
            ), 0.0
        )
    ).filter(TxModel.user_id == getattr(current_user, "id", 1)).scalar()

    return BalanceOut(saldo=float(total or 0.0))
