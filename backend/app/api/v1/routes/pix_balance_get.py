from datetime import datetime

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction


router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

# TODO: ligar com auth/JWT e X-User-Email de verdade.
USER_FIXO_ID = 1


@router.get("/balance")
def get_pix_balance(
    x_user_email: str = Header(..., alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    """
    Versão GET da rota /api/v1/pix/balance.

    Por enquanto:
    - Ignora o e-mail e usa um usuário fixo (USER_FIXO_ID).
    - Calcula o saldo a partir das transações PixTransaction.
    - Devolve payload normalizado para painel e IA 3.0:

    {
      "saldo": number,
      "source": "lab" | "real",
      "updated_at": ISO8601,
      "saldo_atual": number,
      "entradas_mes": number,
      "saidas_mes": number,
      "debug_error": str | null
    }
    """
    debug_error = None

    try:
        # Entradas: PIX recebidos (e qualquer tipo marcado como 'entrada')
        entradas = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
            .filter(
                PixTransaction.user_id == USER_FIXO_ID,
                PixTransaction.tipo.in_(["recebimento", "entrada"]),
            )
            .scalar()
            or 0.0
        )

        # Saídas: PIX enviados (e qualquer tipo marcado como 'saida')
        saidas = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
            .filter(
                PixTransaction.user_id == USER_FIXO_ID,
                PixTransaction.tipo.in_(["envio", "saida"]),
            )
            .scalar()
            or 0.0
        )

        saldo = float(entradas - saidas)
        source = "real"
    except Exception as e:
        print("[AUREA PIX] erro em get_pix_balance:", e)
        debug_error = str(e)
        entradas = 0.0
        saidas = 0.0
        saldo = 0.0
        source = "lab"

    return {
        "saldo_atual": float(saldo),
        "entradas_mes": float(entradas),
        "saidas_mes": float(saidas),
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
