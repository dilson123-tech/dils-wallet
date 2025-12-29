from __future__ import annotations
from datetime import datetime, timezone

from datetime import date, timedelta, datetime
import calendar
import math
import os
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models import User
from app.utils.authz import get_current_user

router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

AUREA_DEBUG = os.getenv("AUREA_DEBUG", "0") == "1"


def _sf(x: float) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else 0.0
    except Exception:
        return 0.0


def _ultimos_7d(db: Session, user_id: int) -> List[Dict[str, Any]]:
    hoje = date.today()
    day_map: Dict[str, Dict[str, Any]] = {}
    for i in range(6, -1, -1):
        d = hoje - timedelta(days=i)
        k = d.isoformat()
        day_map[k] = {"dia": k, "entradas": 0.0, "saidas": 0.0, "saldo_dia": 0.0}

    rows = (
        db.query(PixTransaction)
        .filter(PixTransaction.user_id == user_id)
        .order_by(PixTransaction.id.desc())
        .limit(500)
        .all()
    )

    for tx in rows:
        dt = getattr(tx, "timestamp", None) or getattr(tx, "created_at", None)
        if not dt:
            dt = datetime.combine(hoje, datetime.min.time())
        try:
            dia = dt.date().isoformat()
        except Exception:
            try:
                dia = datetime.fromisoformat(str(dt)).date().isoformat()
            except Exception:
                continue

        if dia not in day_map:
            continue

        v = _sf(getattr(tx, "valor", 0.0) or 0.0)
        tipo = str(getattr(tx, "tipo", "") or "").lower()
        if tipo in ("recebimento", "entrada"):
            day_map[dia]["entradas"] += v
        elif tipo in ("envio", "saida"):
            day_map[dia]["saidas"] += v

    for k in list(day_map.keys()):
        day_map[k]["entradas"] = _sf(day_map[k]["entradas"])
        day_map[k]["saidas"] = _sf(day_map[k]["saidas"])
        day_map[k]["saldo_dia"] = _sf(day_map[k]["entradas"] - day_map[k]["saidas"])

    return list(day_map.values())


@router.get("/balance")
@router.get("/balance/super2")
def get_pix_balance(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Produção: saldo/entradas/saídas + últimos 7 dias do usuário autenticado (JWT válido).
    Sem X-User-Email. Sem decode unverified. Sem USER_FIXO_ID.
    """
    user_id = int(current_user.id)

    entradas = (
        db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
        .filter(
            PixTransaction.user_id == user_id,
            PixTransaction.tipo.in_(["recebimento", "entrada"]),
        )
        .scalar()
        or 0.0
    )

    saidas = (
        db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
        .filter(
            PixTransaction.user_id == user_id,
            PixTransaction.tipo.in_(["envio", "saida"]),
        )
        .scalar()
        or 0.0
    )

    saldo = _sf(float(entradas)) - _sf(float(saidas))
    ult7 = _ultimos_7d(db, user_id)

    payload = {
        "saldo": saldo,
        "saldo_atual": saldo,  # compat
        "entradas_mes": _sf(entradas),
        "saidas_mes": _sf(saidas),
        "ultimos_7d": ult7,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "source": "real",
    }

    if AUREA_DEBUG and request.query_params.get("debug") == "1":
        payload["debug_user_id"] = user_id
        payload["debug_tx_total"] = int(
            db.query(func.count(PixTransaction.id)).filter(PixTransaction.user_id == user_id).scalar() or 0
        )

    return payload


@router.get("/forecast")
@router.get("/forecast_lab_old")
def get_pix_forecast(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Produção: previsão do mês com base no histórico PIX do usuário autenticado.
    """
    user_id = int(current_user.id)

    rows = db.query(PixTransaction).filter(PixTransaction.user_id == user_id).all()

    entradas = 0.0
    saidas = 0.0
    for t in rows:
        valor = _sf(getattr(t, "valor", 0.0) or 0.0)
        tipo = str(getattr(t, "tipo", "") or "").lower()
        if tipo in ("recebimento", "entrada"):
            entradas += valor
        elif tipo in ("envio", "saida"):
            saidas += valor

    saldo_atual = _sf(entradas - saidas)

    agora = datetime.now(timezone.utc)
    dia_atual = max(agora.day, 1)
    dias_mes = calendar.monthrange(agora.year, agora.month)[1]
    media_saidas_dia = _sf(saidas / dia_atual) if dia_atual > 0 else 0.0

    previsao_saidas_total = _sf(media_saidas_dia * dias_mes)
    previsao_fim_mes = _sf(entradas - previsao_saidas_total)

    if previsao_fim_mes >= 0:
        if entradas > 0 and previsao_fim_mes >= 0.2 * entradas:
            nivel_risco = "ok"
        else:
            nivel_risco = "atencao"
    else:
        if previsao_fim_mes >= -200:
            nivel_risco = "alerta"
        else:
            nivel_risco = "critico"

    if nivel_risco == "ok":
        analise = "Projeção saudável até o fim do mês. Você está gastando abaixo do que entra via PIX."
        recomendacoes = [
            "Continue acompanhando entradas e saídas pelo painel.",
            "Mantenha uma reserva mínima para imprevistos.",
            "Se possível, direcione parte do saldo para uma reserva recorrente.",
        ]
    elif nivel_risco == "atencao":
        analise = "Você fecha positivo, mas apertado. O ritmo de gastos está perto do limite do que entra."
        recomendacoes = [
            "Evite gastos não essenciais nos próximos dias.",
            "Revise as principais saídas do mês e reduza o que der.",
            "Acompanhe a IA 3.0 para ajustar o ritmo de gastos.",
        ]
    elif nivel_risco == "alerta":
        analise = "Cenário de alerta: mantendo o ritmo, você pode fechar no vermelho ou muito próximo de zero."
        recomendacoes = [
            "Reduza imediatamente gastos variáveis e de lazer.",
            "Segure compras não essenciais.",
            "Use a IA 3.0 para identificar onde cortar gastos.",
        ]
    else:
        analise = "Cenário crítico: pelo ritmo atual, a projeção indica fechamento no negativo de forma mais pesada."
        recomendacoes = [
            "Corte tudo que não for essencial até recuperar o equilíbrio.",
            "Avalie renegociar parcelamentos/dívidas, se houver.",
            "Busque aumentar entradas (serviços extras, recebíveis).",
        ]

    payload = {
        "saldo_atual": saldo_atual,
        "entradas_mes": _sf(entradas),
        "saidas_mes": _sf(saidas),
        "previsao_fim_mes": previsao_fim_mes,
        "nivel_risco": nivel_risco,
        "analise": analise,
        "recomendacoes": recomendacoes,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
    }

    if AUREA_DEBUG and request.query_params.get("debug") == "1":
        payload["debug_user_id"] = user_id

    return payload
