from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import models, database
from app.security import get_current_user


def _tx_to_dict(t):
    d = {
        "id": getattr(t, "id", None),
        "user_id": getattr(t, "user_id", None),
        "tipo": getattr(t, "tipo", None),
        "valor": float(getattr(t, "valor", 0) or 0),
        "descricao": getattr(t, "description", None) or getattr(t, "descricao", None),
        "referencia": getattr(t, "referencia", None) or getattr(t, "reference", None),
        "created_at": getattr(t, "created_at", None) or datetime.utcnow(),
    }
    if hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d


class TransactionCreate(BaseModel):
    tipo: str
    valor: Union[float, str]
    descricao: Optional[str] = None


class BalanceOut(BaseModel):
    saldo: Union[float, str]


router = APIRouter(tags=["transactions"])
ALLOWED_TYPES = {"deposito", "saque", "transferencia"}


@router.post("")
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    t = (payload.tipo or "").strip().lower()
    if t not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"tipo inválido. Use: {sorted(ALLOWED_TYPES)}")
    # aceita string/number e valida > 0
    try:
        v = float(payload.valor)
    except Exception:
        raise HTTPException(status_code=400, detail="valor inválido")
    if v <= 0:
        raise HTTPException(status_code=400, detail="valor deve ser > 0")

    tx = models.Transaction(
        user_id=current_user.id,
        tipo=t,
        valor=v,
        referencia=(getattr(payload, "referencia", None) or getattr(payload, "reference", None) or "") or "",
        descricao=getattr(payload, "descricao", None),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return _tx_to_dict(tx)


@router.get("")
def list_transactions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    items = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_tx_to_dict(t) for t in items]


@router.get("/balance")
def get_balance(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    from sqlalchemy import func, case

    q = db.query(
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
    saldo = float(q.scalar() or 0.0)
    return BalanceOut(saldo=saldo)


@router.get("/paged")
def list_transactions_paged(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    base_q = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    total = base_q.count()
    items = (
        base_q.order_by(models.Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size
    return {
        "items": [_tx_to_dict(t) for t in items],
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": (page * page_size) < total,
            "has_prev": page > 1,
        },
    }
