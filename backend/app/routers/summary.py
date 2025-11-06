from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.database import get_db
from app.models.pix_transaction import PixTransaction  # seu modelo

router = APIRouter(prefix="/api/v1/ai", tags=["summary"])

# Tentativas de nomes por campo
_AMOUNT_CANDS = ["amount", "valor,amount", "valor", "value", "quantia", "ammount"]
_DIR_CANDS    = ["direction", "tipo", "kind", "type", "direcao"]
_TIME_CANDS   = ["created_at", "timestamp", "data_hora", "data", "created", "dt"]

def _first_attr_or_none(model, names):
    for name in names:
        # permitir fallback "a,b" para compat com migrações (ex.: "valor,amount")
        for n in map(str.strip, name.split(",")):
            if hasattr(model, n):
                return getattr(model, n)
    return None

@router.get("/summary")
def get_ai_summary(db: Session = Depends(get_db)):
    try:
        cols = PixTransaction.__table__.columns.keys()
        amount_col = _first_attr_or_none(PixTransaction, _AMOUNT_CANDS)
        dir_col    = _first_attr_or_none(PixTransaction, _DIR_CANDS)
        time_col   = _first_attr_or_none(PixTransaction, _TIME_CANDS)

        if amount_col is None:
            raise HTTPException(
                status_code=500,
                detail=f"summary_error: campo de valor não encontrado. "
                       f"Tente renomear para um de { _AMOUNT_CANDS } "
                       f"(colunas existentes: {list(cols)})"
            )

        # janela de 24h (UTC)
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=24)

        # saldo total
        saldo_total = db.query(func.coalesce(func.sum(amount_col), 0)).scalar() or 0

        # filtro de tempo, se houver coluna temporal
        time_filter = []
        if time_col is not None:
            time_filter = [time_col >= since]

        # Estratégia:
        # - Se tiver coluna de direção, usamos ("IN"/"OUT", etc.)
        # - Senão, tratamos entradas como amount > 0 e saídas como amount < 0 (módulo)
        if dir_col is not None:
            entradas_24h = (
                db.query(func.coalesce(func.sum(amount_col), 0))
                  .filter(dir_col.in_(["IN", "in", "entrada", "ENTRADA", "credit", "CREDIT"]))
                  .filter(*time_filter)
                  .scalar() or 0
            )
            saidas_24h = (
                db.query(func.coalesce(func.sum(amount_col), 0))
                  .filter(dir_col.in_(["OUT", "out", "saida", "SAIDA", "debit", "DEBIT"]))
                  .filter(*time_filter)
                  .scalar() or 0
            )
            # quantidade total no período
            qtd_24h = (
                db.query(func.count(PixTransaction.__table__.c[list(cols)[0]]))
                  .filter(*time_filter)
                  .scalar() or 0
            )
            # se saídas forem negativas no seu esquema, normalizamos para positivo
            try:
                saidas_24h = abs(float(saidas_24h))
            except Exception:
                pass
        else:
            # Sem direção: separa por sinal do amount
            entradas_24h = (
                db.query(func.coalesce(func.sum(amount_col), 0))
                  .filter(amount_col > 0)
                  .filter(*time_filter)
                  .scalar() or 0
            )
            saidas_brutas = (
                db.query(func.coalesce(func.sum(amount_col), 0))
                  .filter(amount_col < 0)
                  .filter(*time_filter)
                  .scalar() or 0
            )
            saidas_24h = abs(float(saidas_brutas))
            qtd_24h = (
                db.query(func.count(PixTransaction.__table__.c[list(cols)[0]]))
                  .filter(*time_filter)
                  .scalar() or 0
            )

        return {
            "saldo_atual": float(saldo_total),
            "ultimas_24h": {
                "entradas": float(entradas_24h),
                "saidas": float(saidas_24h),
                "qtd": int(qtd_24h),
            },
            "meta": {
                "amount_col": getattr(amount_col, "key", str(amount_col)),
                "dir_col": getattr(dir_col, "key", None),
                "time_col": getattr(time_col, "key", None),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        # Expõe colunas para facilitar debug
        cols = getattr(PixTransaction.__table__, "columns", None)
        keys = list(cols.keys()) if cols is not None else []
        raise HTTPException(status_code=500, detail=f"summary_error: {e}; cols={keys}")
