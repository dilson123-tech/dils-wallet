from __future__ import annotations

import base64, json, os, math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query, Header, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.utils.authz import require_customer
from app.api.v1.schemas.errors import ErrorResponse, OPENAPI_422

router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])

def _pick_date_col():
    candidates = ["created_at", "created", "timestamp", "data", "dia", "date"]
    cols = set(PixTransaction.__table__.columns.keys())
    for name in candidates:
        if name in cols:
            return getattr(PixTransaction, name)
    return None

DATE_COL = _pick_date_col()

class PixHistoryDay(BaseModel):
    dia: str
    entradas: float = 0.0
    saidas: float = 0.0

class PixHistoryItem(BaseModel):
    user_id: Optional[int] = None
    id: int
    tipo: str
    valor: float
    taxa_percentual: Optional[float] = None
    taxa_valor: Optional[float] = None
    timestamp: Optional[str] = None
    descricao: Optional[str] = None
    valor_liquido: Optional[float] = None

class PixHistoryResponse(BaseModel):
    dias: List[PixHistoryDay]
    history: List[PixHistoryItem]
    updated_at: str = Field(..., description="ISO8601 UTC")
    source: str = Field(default="real")

@router.get("/history", response_model=PixHistoryResponse, responses={401: {"model": ErrorResponse, "description": "Unauthorized"}, 422: OPENAPI_422, 500: {"model": ErrorResponse, "description": "Internal Server Error"}})
def get_pix_history(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
    current_user = Depends(require_customer),
):
    q = db.query(PixTransaction)

    user_id = getattr(current_user, "id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token ausente.")
    q = q.filter(PixTransaction.user_id == int(user_id))

    if DATE_COL is not None:
        q = q.order_by(DATE_COL.desc())

    transactions = q.offset(offset).limit(limit).all()

    dias_map: Dict[str, Dict[str, float]] = {}
    for t in transactions:
        dt = getattr(t, DATE_COL.key) if DATE_COL is not None else getattr(t, "dia", None) or getattr(t, "data", None)
        dia = dt.strftime("%Y-%m-%d") if dt else "sem-data"

        if dia not in dias_map:
            dias_map[dia] = {"entradas": 0.0, "saidas": 0.0}

        tipo = str(getattr(t, "tipo", "") or "").lower()
        v = float(getattr(t, "valor", 0.0) or 0.0)
        if tipo in ("recebimento", "entrada", "recebido"):
            dias_map[dia]["entradas"] += v
        else:
            dias_map[dia]["saidas"] += v

    dias_out = [{"dia": k, "entradas": float(v["entradas"]), "saidas": float(v["saidas"])} for k, v in dias_map.items()]

    history_items: List[Dict[str, Any]] = []
    for tx in transactions:
        dt2 = getattr(tx, DATE_COL.key) if DATE_COL is not None else getattr(tx, "timestamp", None) or getattr(tx, "created_at", None)
        ts = None
        if dt2 is not None:
            try:
                ts = dt2.isoformat() if hasattr(dt2, "isoformat") else str(dt2)
            except Exception:
                ts = str(dt2)

        history_items.append({
            "user_id": getattr(tx, "user_id", None),
            "id": int(getattr(tx, "id", 0) or 0),
            "tipo": str(getattr(tx, "tipo", "") or ""),
            "valor": float(getattr(tx, "valor", 0.0) or 0.0),
            "taxa_percentual": float(getattr(tx, "taxa_percentual", 0.0) or 0.0) if hasattr(tx, "taxa_percentual") else None,
            "taxa_valor": float(getattr(tx, "taxa_valor", 0.0) or 0.0) if hasattr(tx, "taxa_valor") else None,
            "timestamp": ts,
            "descricao": getattr(tx, "descricao", None),
            "valor_liquido": float(getattr(tx, "valor_liquido", getattr(tx, "valor", 0.0)) or 0.0) if hasattr(tx, "valor_liquido") else None,
        })

    return {
        "dias": dias_out,
        "history": history_items,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "real",
    }
