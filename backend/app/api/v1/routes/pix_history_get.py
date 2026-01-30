from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query, Header, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import DateTime, Date

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.utils.authz import require_customer
from app.api.v1.schemas.errors import ErrorResponse, OPENAPI_422


router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])


def _sf(x: Any) -> float:
    """safe-float: aceita Decimal/str/None, tolera '20%' e '0,2'."""
    if x is None:
        return 0.0
    if isinstance(x, str):
        s = x.strip().replace("%", "").replace(",", ".")
        if not s:
            return 0.0
        try:
            v = float(s)
            return v if math.isfinite(v) else 0.0
        except Exception:
            return 0.0
    try:
        v = float(x)
        return v if math.isfinite(v) else 0.0
    except Exception:
        return 0.0


def _to_day_key(val: Any) -> str:
    """Converte datetime/date/str/int -> 'YYYY-MM-DD' (bem tolerante)."""
    if val is None:
        return "sem-data"

    # datetime/date
    try:
        # datetime tem .date()
        if hasattr(val, "date"):
            d = val.date() if hasattr(val, "hour") else val  # date não tem hour
            return d.isoformat()
    except Exception:
        pass

    # epoch seconds (int/float)
    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc).date().isoformat()
        except Exception:
            return "sem-data"

    # string ISO
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return "sem-data"
        s2 = s.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s2).date().isoformat()
        except Exception:
            # fallback: tenta usar só o prefixo YYYY-MM-DD
            return s[:10] if len(s) >= 10 else s

    return str(val)[:10]


def _to_ts(val: Any) -> Optional[str]:
    """Converte datetime/date/str/int -> ISO string (ou None)."""
    if val is None:
        return None

    try:
        if hasattr(val, "isoformat"):
            return val.isoformat()
    except Exception:
        pass

    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc).isoformat()
        except Exception:
            return str(val)

    if isinstance(val, str):
        s = val.strip()
        return s or None

    return str(val)


def _pick_date_col():
    """
    Escolhe uma coluna de data *de verdade* (Date/DateTime) se existir.
    Evita pegar coluna 'timestamp' string e depois quebrar em strftime().
    """
    candidates = ["created_at", "created", "timestamp", "data", "dia", "date"]
    cols = PixTransaction.__table__.columns
    for name in candidates:
        col = cols.get(name)
        if col is None:
            continue
        # só aceita tipos Date/DateTime (ou subclasses)
        if isinstance(col.type, (DateTime, Date)):
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
    descricao: Optional[Any] = None
    valor_liquido: Optional[float] = None


class PixHistoryResponse(BaseModel):
    dias: List[PixHistoryDay]
    history: List[PixHistoryItem]
    updated_at: str = Field(..., description="ISO8601 UTC")
    source: str = Field(default="real")


@router.get(
    "/history",
    response_model=PixHistoryResponse,
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
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
    current_user=Depends(require_customer),
):
    user_id = getattr(current_user, "id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token ausente.")

    try:
        q = db.query(PixTransaction).filter(PixTransaction.user_id == int(user_id))
        if DATE_COL is not None:
            q = q.order_by(DATE_COL.desc())
        else:
            # fallback: tenta por id (mais previsível)
            if "id" in PixTransaction.__table__.columns.keys():
                q = q.order_by(PixTransaction.id.desc())

        transactions = q.offset(offset).limit(limit).all()

        dias_map: Dict[str, Dict[str, float]] = {}

        for t in transactions:
            dt_val = None
            if DATE_COL is not None:
                dt_val = getattr(t, DATE_COL.key, None)
            else:
                dt_val = getattr(t, "dia", None) or getattr(t, "data", None) or getattr(t, "timestamp", None) or getattr(t, "created_at", None)

            dia = _to_day_key(dt_val)
            if dia not in dias_map:
                dias_map[dia] = {"entradas": 0.0, "saidas": 0.0}

            tipo = str(getattr(t, "tipo", "") or "").lower()
            v = _sf(getattr(t, "valor", 0.0))

            if tipo in ("recebimento", "entrada", "recebido"):
                dias_map[dia]["entradas"] += v
            else:
                dias_map[dia]["saidas"] += v

        dias_out = [
            {"dia": k, "entradas": float(v["entradas"]), "saidas": float(v["saidas"])}
            for k, v in dias_map.items()
        ]

        history_items: List[Dict[str, Any]] = []
        for tx in transactions:
            dt2 = None
            if DATE_COL is not None:
                dt2 = getattr(tx, DATE_COL.key, None)
            else:
                dt2 = getattr(tx, "timestamp", None) or getattr(tx, "created_at", None) or getattr(tx, "dia", None) or getattr(tx, "data", None)

            history_items.append(
                {
                    "user_id": getattr(tx, "user_id", None),
                    "id": int(getattr(tx, "id", 0) or 0),
                    "tipo": str(getattr(tx, "tipo", "") or ""),
                    "valor": _sf(getattr(tx, "valor", 0.0)),
                    "taxa_percentual": _sf(getattr(tx, "taxa_percentual", None)) if hasattr(tx, "taxa_percentual") else None,
                    "taxa_valor": _sf(getattr(tx, "taxa_valor", None)) if hasattr(tx, "taxa_valor") else None,
                    "timestamp": _to_ts(dt2),
                    "descricao": getattr(tx, "descricao", None),
                    "valor_liquido": _sf(getattr(tx, "valor_liquido", getattr(tx, "valor", 0.0))) if hasattr(tx, "valor_liquido") else None,
                }
            )

        return {
            "dias": dias_out,
            "history": history_items,
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "real",
        }

    except HTTPException:
        raise
    except Exception as e:
        rid = request.headers.get("x-request-id") or request.headers.get("X-Request-Id") or ""
        print(f"[PIX_HISTORY] error rid={rid} user_id={user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
