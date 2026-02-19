from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .... import models, database
from ....security import get_current_user
from ....services.transaction_service import create_transaction, get_summary


def _tx_to_dict(t):
    return {
        "id": t.id,
        "user_id": t.user_id,
        "tipo": "deposito" if t.kind == "credit" else "saque",
        "valor": float(t.amount),
        "descricao": t.description,
        "referencia": t.description,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


class TransactionCreate(BaseModel):
    tipo: str
    valor: Union[float, str]
    descricao: Optional[str] = None
    referencia: Optional[str] = None


router = APIRouter(tags=["transactions"])


@router.post("")
def create_transaction_route(
    payload: TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    tx = create_transaction(payload, db, current_user)
    return _tx_to_dict(tx)


@router.get("/balance")
def summary(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    return get_summary(db, current_user)
