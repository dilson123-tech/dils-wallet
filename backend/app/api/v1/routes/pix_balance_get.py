from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models.user_main import User as UserMain

router = APIRouter(prefix="/api/v1/pix", tags=["pix"])


@router.get("/balance")
def get_pix_balance(
    x_user_email: str = Header(..., alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    """
    Versão GET da rota /api/v1/pix/balance.
    Usa o e-mail do header X-User-Email para localizar o usuário
    e calcula o saldo a partir das transações de entrada (entrada) e saída (saida).
    """

    user = db.query(UserMain).filter(UserMain.username == x_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    entradas = (
        db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
        .filter(
            PixTransaction.user_id == user.id,
            PixTransaction.tipo == "entrada",
        )
        .scalar()
        or 0.0
    )

    saidas = (
        db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
        .filter(
            PixTransaction.user_id == user.id,
            PixTransaction.tipo == "saida",
        )
        .scalar()
        or 0.0
    )

    saldo = float(entradas - saidas)

    return {
        "saldo": saldo,
        "entradas_mes": float(entradas),
        "saidas_mes": float(saidas),
    }
