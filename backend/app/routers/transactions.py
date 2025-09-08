from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Optional
from .. import models, schemas, database, auth

router = APIRouter(prefix="/transactions", tags=["transactions"])

ALLOWED_TYPES = {"deposito", "saque", "transferencia"}

@router.post("/", response_model=schemas.TransactionResponse)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    tipo = payload.tipo.lower().strip()
    if tipo not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"tipo inválido. Use: {sorted(list(ALLOWED_TYPES))}")
    if payload.valor is None or payload.valor <= 0:
        raise HTTPException(status_code=400, detail="valor deve ser > 0")

    tx = models.Transaction(
        user_id=current_user.id,
        tipo=tipo,
        valor=payload.valor,
        referencia=payload.referencia,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.get("/", response_model=List[schemas.TransactionResponse])
def list_transactions(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    tipo: Optional[str] = Query(None, description="deposito|saque|transferencia"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    if tipo:
        q = q.filter(models.Transaction.tipo == tipo.lower().strip())
    q = q.order_by(models.Transaction.criado_em.desc()).offset(offset).limit(limit)
    return q.all()

@router.get("/balance")
def get_balance(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # saldo = soma(depositos) - soma(saques) - soma(transferencias de saída) + (no futuro: recebimentos)
    value = db.query(
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
    ).filter(models.Transaction.user_id == current_user.id).scalar()
    return {"user_id": current_user.id, "balance": float(value)}
