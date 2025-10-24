from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date
from app import database as database  # usa database.get_db

router = APIRouter(prefix="/pix", tags=["PIX"])

@router.get("/daily-summary", response_model=List[Dict[str, Any]])
def get_daily_summary(
    *,
    db: Session = Depends(database.get_db),
    start: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD, UTC)"),
    end: Optional[date]   = Query(None, description="Data final (YYYY-MM-DD, UTC, inclusiva)")
):
    """
    Retorna série diária da MV `pix_daily_summary` com filtros opcionais.
    Usa parâmetros nomeados (:start, :end) — compatível com SQLAlchemy.
    """
    sql = text("""
        SELECT day_utc, total_count, total_amount, avg_amount, min_amount, max_amount,
               distinct_senders, distinct_receivers, accounts_active
        FROM pix_daily_summary
        WHERE (:start IS NULL OR day_utc >= :start)
          AND (:end   IS NULL OR day_utc <= :end)
        ORDER BY day_utc ASC
    """)
    res = db.execute(sql, {"start": start, "end": end}).mappings().all()
    return [dict(r) for r in res]

@router.post("/daily-summary/refresh", status_code=202)
def refresh_daily_summary(*, db: Session = Depends(database.get_db)):
    db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY pix_daily_summary;"))
    db.commit()
    return {"status": "refresh started"}
