from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models.user_main import User

# mesmo padrão da rota original de balance
router = APIRouter(prefix="/api/v1/pix", tags=["pix"])


@router.get("/balance/super2")
def get_pix_balance_super2(
    x_user_email: str = Header(..., alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    """
    Versão Super2 da rota /api/v1/pix/balance.

    - Usa o mesmo cálculo de saldo, entradas e saídas da rota original.
    - Adiciona um campo `ultimos_7d` para o painel Super2.
    """

    # --- mesmo começo da get_pix_balance ---
    user = db.query(User).filter(User.email == x_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    entradas = (
        db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
        .filter(
            PixTransaction.user_id == user.id,
            PixTransaction.tipo.in_(["recebimento", "entrada"]),
        )
        .scalar()
        or 0.0
    )

    saidas = (
        db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
        .filter(
            PixTransaction.user_id == user.id,
            PixTransaction.tipo.in_(["envio", "saida"]),
        )
        .scalar()
        or 0.0
    )

    saldo = float(entradas - saidas)

    # --- mock simples dos últimos 7 dias (por enquanto tudo zero) ---
    hoje = date.today()
    ultimos_7d = []
    for i in range(6, -1, -1):
        d = hoje - timedelta(days=i)
        ultimos_7d.append(
            {
                "dia": d.isoformat(),
                "entradas": 0.0,
                "saidas": 0.0,
            }
        )

    return {
        "saldo_atual": float(saldo),
        "entradas_mes": float(entradas),
        "saidas_mes": float(saidas),
        "ultimos_7d": ultimos_7d,
    }
