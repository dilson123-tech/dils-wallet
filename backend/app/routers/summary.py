from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction

router = APIRouter(prefix="/api/v1/ai", tags=["summary"])

@router.get("/summary")
def get_ai_summary(
    hours: int = Query(24, ge=1, le=24*30, description="Janela em horas (1..720)"),
    db: Session = Depends(get_db),
):
    """
    Resumo de PIX:
    - saldo_atual: soma de todos os valores (positivo entra, negativo sai)
    - entradas_total / saidas_total: totais absolutos no histórico
    - ultimas_<hours>h: entradas, saídas e quantidade de transações na janela
    Campos fixos: valor (Numeric), tipo ('IN'/'OUT'), timestamp (datetime)
    """
    try:
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=hours)

        # totais históricos
        saldo_total = db.query(func.coalesce(func.sum(PixTransaction.valor), 0)).scalar() or 0

        entradas_total = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0))
              .filter(PixTransaction.tipo.in_(["IN","in","ENTRADA","entrada","credit","CREDIT"]))
              .scalar() or 0
        )

        saidas_total = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0))
              .filter(PixTransaction.tipo.in_(["OUT","out","SAIDA","saida","debit","DEBIT"]))
              .scalar() or 0
        )
        # normaliza saídas como positivo se estiver negativo no banco
        try:
            saidas_total = abs(float(saidas_total))
        except Exception:
            pass

        # últimas N horas
        entradas_h = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0))
              .filter(PixTransaction.tipo.in_(["IN","in","ENTRADA","entrada","credit","CREDIT"]))
              .filter(PixTransaction.timestamp >= since)
              .scalar() or 0
        )

        saidas_h_raw = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0))
              .filter(PixTransaction.tipo.in_(["OUT","out","SAIDA","saida","debit","DEBIT"]))
              .filter(PixTransaction.timestamp >= since)
              .scalar() or 0
        )
        saidas_h = abs(float(saidas_h_raw))

        qtd_h = (
            db.query(func.count(PixTransaction.id))
              .filter(PixTransaction.timestamp >= since)
              .scalar() or 0
        )

        return {
            "saldo_atual": float(saldo_total),
            "entradas_total": float(entradas_total),
            "saidas_total": float(saidas_total),
            "ultimas_horas": int(hours),
            "ultimas_janela": {
                "entradas": float(entradas_h),
                "saidas": float(saidas_h),
                "qtd": int(qtd_h),
                "desde": since.isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"summary_error: {e}")
