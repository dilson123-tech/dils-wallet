from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date
from backend.app import database as database  # ajuste se seu caminho de deps for outro

router = APIRouter(prefix="/pix", tags=["PIX"])

@router.get("/daily-summary", response_model=List[Dict[str, Any]])
def get_daily_summary(
    *,
    db: Session = Depends(database.get_db),
    start: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD, UTC)"),
    end: Optional[date]   = Query(None, description="Data final (YYYY-MM-DD, UTC, inclusiva)")
):
    """
    Retorna série diária de métricas de PIX a partir da view materializada `pix_daily_summary`.
    Filtros por `start` e `end` (UTC). Ordenado crescente por dia.
    """
    sql = """
        SELECT day_utc, total_count, total_amount, avg_amount, min_amount, max_amount,
               distinct_senders, distinct_receivers, accounts_active
        FROM pix_daily_summary
        WHERE ($1::date IS NULL OR day_utc >= $1::date)
          AND ($2::date IS NULL OR day_utc <= $2::date)
        ORDER BY day_utc ASC
    """
    res = db.execute(text(sql).bindparams(start, end)).mappings().all()
    return [dict(r) for r in res]

@router.post("/daily-summary/refresh", status_code=202)
def refresh_daily_summary(*, db: Session = Depends(database.get_db)):
    """
    Dispara refresh CONCURRENTLY da materialized view (não bloqueia leitura).
    """
    db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY pix_daily_summary;"))
    db.commit()
    return {"status": "refresh started"}
