from decimal import Decimal
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction

router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

USER_FIXO_ID = 1  # TODO: depois ligar com auth/jwt

@router.get("/balance")
def get_balance(db: Session = Depends(get_db)):
    """
    Retorna o saldo PIX calculado:
    entradas somam, saídas subtraem.
    """
    rows = (
        db.query(PixTransaction)
        .filter(PixTransaction.user_id == USER_FIXO_ID)
        .all()
    )

    saldo = 0.0
    for t in rows:
        if t.tipo == "entrada":
            saldo += float(t.valor)
        else:
            saldo -= float(t.valor)

    return JSONResponse(content=jsonable_encoder({"saldo": saldo}, custom_encoder={Decimal: float}))
@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    """
    Retorna as últimas transações do usuário.
    """
    txs = (
        db.query(PixTransaction)
        .filter(PixTransaction.user_id == USER_FIXO_ID)
        .order_by(PixTransaction.id.desc())
        .limit(20)
        .all()
    )

    result = [
        {
            "id": t.id,
            "tipo": t.tipo,
            "valor": float(t.valor),
            "descricao": t.descricao or "",
        }
        for t in txs
    ]

    return result
