from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.utils.authz import require_customer
from app.models import Transaction, User

router = APIRouter()

@router.get("/api/v1/wallet/balance")
def get_balance(current_user: User = Depends(require_customer),
                db: Session = Depends(get_db)):
    """
    Calcula saldo do usuário = soma(credit) - soma(debit)
    """
    rows = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .all()
    )

    saldo = Decimal("0.00")
    for tx in rows:
        if tx.kind == "credit":
            saldo += Decimal(tx.amount)
        elif tx.kind == "debit":
            saldo -= Decimal(tx.amount)

    return {
        "user_id": current_user.id,
        "balance": f"{saldo:.2f}"
    }

@router.get("/api/v1/wallet/history")
def get_history(current_user: User = Depends(require_customer),
                db: Session = Depends(get_db)):
    """
    Retorna lista das últimas transações do usuário autenticado.
    """
    rows = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )

    history = []
    for tx in rows:
        history.append({
            "id": tx.id,
            "kind": tx.kind,
            "description": tx.description,
            "amount": str(tx.amount),
            "created_at": tx.created_at.isoformat(),
        })

    return {
        "user_id": current_user.id,
        "history": history
    }
