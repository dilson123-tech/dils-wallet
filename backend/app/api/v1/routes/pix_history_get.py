from __future__ import annotations

import os
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.utils.authz import require_customer
from app.api.v1.schemas.errors import ErrorResponse, OPENAPI_422

router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

AUREA_DEBUG = os.getenv("AUREA_DEBUG", "0").strip().lower() in ("1", "true", "yes", "on")


def _to_dt(v) -> Optional[datetime]:
    """Converte v (datetime/date/str/int) para datetime (best-effort)."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime.combine(v, datetime.min.time())
    if isinstance(v, (int, float)):
        try:
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        # isoformat com Z
        try:
            s2 = s[:-1] + "+00:00" if s.endswith("Z") else s
            return datetime.fromisoformat(s2)
        except Exception:
            return None
    return None


def _pick_date_value(tx: PixTransaction):
    """Tenta achar um campo de data no tx sem quebrar."""
    for name in ("created_at", "created", "timestamp", "data", "dia", "date"):
        if hasattr(tx, name):
            val = getattr(tx, name, None)
            if val is not None:
                return val
    return None


def _sf(x) -> float:
    try:
        return float(x or 0.0)
    except Exception:
        return 0.0


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
    dias: List[PixHistoryDay] = []
    history: List[PixHistoryItem] = []
    # compat para front antigo (se algum lugar ainda usa `.items`)
    items: List[PixHistoryItem] = []
    updated_at: str = Field(..., description="ISO8601 UTC")
    source: str = Field(default="real")


@router.get(
    "/history",
    response_model=PixHistoryResponse,
    response_model_exclude_none=True,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        422: OPENAPI_422,
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_pix_history(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(require_customer),
):
    try:
        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token ausente.")

        q = db.query(PixTransaction).filter(PixTransaction.user_id == int(user_id))

        # ordenação: tenta usar uma coluna “date-like” se existir
        # (se não existir, ordena por id desc)
        cols = set(PixTransaction.__table__.columns.keys())
        if "created_at" in cols:
            q = q.order_by(getattr(PixTransaction, "created_at").desc())
        elif "timestamp" in cols:
            q = q.order_by(getattr(PixTransaction, "timestamp").desc())
        elif "created" in cols:
            q = q.order_by(getattr(PixTransaction, "created").desc())
        elif "data" in cols:
            q = q.order_by(getattr(PixTransaction, "data").desc())
        elif "dia" in cols:
            q = q.order_by(getattr(PixTransaction, "dia").desc())
        else:
            q = q.order_by(PixTransaction.id.desc())

        transactions = q.offset(offset).limit(limit).all()

        # agregação por dia
        dias_map: Dict[str, Dict[str, float]] = {}
        for t in transactions:
            raw = _pick_date_value(t)
            dt = _to_dt(raw)
            dia = dt.date().isoformat() if dt else "sem-data"

            if dia not in dias_map:
                dias_map[dia] = {"entradas": 0.0, "saidas": 0.0}

            tipo = str(getattr(t, "tipo", "") or "").lower()
            v = _sf(getattr(t, "valor", 0.0))
            if tipo in ("recebimento", "entrada", "recebido"):
                dias_map[dia]["entradas"] += v
            else:
                dias_map[dia]["saidas"] += v

        # ordena dias desc (sem-data fica por último)
        def _day_key(k: str):
            return (k == "sem-data", k)

        dias_out = [
            {"dia": k, "entradas": float(v["entradas"]), "saidas": float(v["saidas"])}
            for k, v in sorted(dias_map.items(), key=lambda kv: _day_key(kv[0]), reverse=False)
        ]

        history_items: List[Dict[str, Any]] = []
        for tx in transactions:
            raw2 = _pick_date_value(tx)
            dt2 = _to_dt(raw2)
            ts = None
            if dt2 is not None:
                try:
                    # normaliza UTC se vier timezone-aware
                    if dt2.tzinfo is None:
                        ts = dt2.isoformat() + "Z"
                    else:
                        ts = dt2.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
                except Exception:
                    ts = str(raw2)

            item = {
                "user_id": getattr(tx, "user_id", None),
                "id": int(getattr(tx, "id", 0) or 0),
                "tipo": str(getattr(tx, "tipo", "") or ""),
                "valor": float(_sf(getattr(tx, "valor", 0.0))),
                "taxa_percentual": float(_sf(getattr(tx, "taxa_percentual", 0.0))) if hasattr(tx, "taxa_percentual") else None,
                "taxa_valor": float(_sf(getattr(tx, "taxa_valor", 0.0))) if hasattr(tx, "taxa_valor") else None,
                "timestamp": ts,
                "descricao": getattr(tx, "descricao", None) if hasattr(tx, "descricao") else getattr(tx, "description", None),
                "valor_liquido": float(_sf(getattr(tx, "valor_liquido", getattr(tx, "valor", 0.0)))) if hasattr(tx, "valor_liquido") else None,
            }
            history_items.append(item)

        updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # ✅ sempre listas (nunca null) + compat `.items`
        return {
            "dias": dias_out or [],
            "history": history_items or [],
            "items": history_items or [],
            "updated_at": updated,
            "source": "real",
        }

    except HTTPException:
        raise
    except Exception as e:
        if AUREA_DEBUG and request.query_params.get("debug") == "1":
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
