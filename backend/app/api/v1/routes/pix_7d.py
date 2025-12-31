from datetime import date, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.utils.authz import require_customer
from app.api.v1.schemas.errors import ErrorResponse, OPENAPI_422

router = APIRouter(prefix="/api/v1/pix", tags=["pix-7d"])


class Pix7dPoint(BaseModel):
    dia: str
    entradas: float
    saidas: float
    saldo_dia: float


class Pix7dResponse(BaseModel):
    ultimos_7d: List[Pix7dPoint]


@router.get("/7d", response_model=Pix7dResponse, responses={401: {"model": ErrorResponse, "description": "Unauthorized"}, 422: OPENAPI_422, 500: {"model": ErrorResponse, "description": "Internal Server Error"}})
def get_pix_7d(db: Session = Depends(get_db), current_user = Depends(require_customer)) -> Pix7dResponse:
    """
    Resumo de todas as transações dos últimos 7 dias, agregadas por dia.
    Usa PixTransaction.timestamp (datetime) e tipo ('recebido', 'envio', etc).
    """
    user_id = getattr(current_user, "id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuário não autenticado.")

    hoje = date.today()
    inicio = hoje - timedelta(days=6)
    fim = hoje + timedelta(days=1)

    rows = (
        db.query(PixTransaction)
        .filter(PixTransaction.timestamp >= inicio)
        .filter(PixTransaction.timestamp < fim)
        .order_by(PixTransaction.timestamp)
        .all()
    )

    # agrega por dia em memória
    mapa: Dict[date, Dict[str, float]] = {}
    for tx in rows:
        dia = tx.timestamp.date()
        if dia not in mapa:
            mapa[dia] = {"entradas": 0.0, "saidas": 0.0}

        tipo = (tx.tipo or "").lower()
        valor = float(tx.valor or 0.0)

        if tipo in ("recebido", "entrada", "in"):
            mapa[dia]["entradas"] += valor
        elif tipo in ("envio", "saida", "saída", "out"):
            mapa[dia]["saidas"] += valor
        else:
            # se não sabemos, tratamos como neutro (pode ajustar depois)
            mapa[dia]["entradas"] += valor

    # monta lista ordenada por dia, com saldo acumulado
    dias_ordenados = sorted(mapa.keys())
    pontos: List[Pix7dPoint] = []
    saldo_acum = 0.0

    for d in dias_ordenados:
        entradas = mapa[d]["entradas"]
        saidas = mapa[d]["saidas"]
        saldo_acum += entradas - saidas

        pontos.append(
            Pix7dPoint(
                dia=d.isoformat(),
                entradas=round(entradas, 2),
                saidas=round(saidas, 2),
                saldo_dia=round(saldo_acum, 2),
            )
        )

    return Pix7dResponse(ultimos_7d=pontos)
