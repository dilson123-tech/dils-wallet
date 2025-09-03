from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, database
from app.security import get_current_user

router = APIRouter(tags=["transactions"])
ALLOWED_TYPES = {"deposito", "saque", "transferencia"}

@router.post("", response_model=schemas.TransactionResponse)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    t = (payload.tipo or "").strip().lower()
    if t not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"tipo inválido. Use: {sorted(ALLOWED_TYPES)}")
    if payload.valor is None or payload.valor <= 0:
        raise HTTPException(status_code=400, detail="valor deve ser > 0")

    tx = models.Transaction(
        user_id=current_user.id,
        tipo=t,
        valor=payload.valor,
        referencia=payload.referencia or "",
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.get("", response_model=List[schemas.TransactionResponse])
def list_transactions(
    skip: int = 0, limit: int = 50,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (db.query(models.Transaction)
              .filter(models.Transaction.user_id == current_user.id)
              .order_by(models.Transaction.id.desc())
.offset(skip).limit(limit).all())

@router.get("/balance", response_model=schemas.BalanceOut)
def get_balance(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    from sqlalchemy import func, case
    q = db.query(
        func.coalesce(func.sum(
            case(
                (models.Transaction.tipo == "deposito", models.Transaction.valor),
                (models.Transaction.tipo == "saque", -models.Transaction.valor),
                (models.Transaction.tipo == "transferencia", -models.Transaction.valor),
                else_=0.0
            )
        ), 0.0)
    ).filter(models.Transaction.user_id == current_user.id)
    saldo = q.scalar() or 0.0
    return schemas.BalanceOut(saldo=saldo)
