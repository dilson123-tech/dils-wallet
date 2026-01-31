from __future__ import annotations

import math
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any, Tuple

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models import User
from app.utils.authz import get_current_user
from app.api.v1.schemas.errors import ErrorResponse, OPENAPI_422


router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])

AUREA_DEBUG = os.getenv("AUREA_DEBUG", "0").strip().lower() in ("1","true","yes","on")

def _as_dia(dt) -> str:
    if dt is None:
        return "sem-data"
    if isinstance(dt, (datetime, date)):
        try:
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return getattr(dt, "isoformat", lambda: "sem-data")()[:10]
    if isinstance(dt, (int, float)):
        try:
            return datetime.fromtimestamp(float(dt), tz=timezone.utc).date().isoformat()
        except Exception:
            return "sem-data"
    s = str(dt).strip()
    if not s:
        return "sem-data"
    try:
        s2 = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s2).date().isoformat()
    except Exception:
        return "sem-data"



def _sf(x: Any) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else 0.0
    except Exception:
        return 0.0


def _dialect(db: Session) -> str:
    try:
        return (db.get_bind().dialect.name or "").lower()
    except Exception:
        return ""


def _pick_table(db: Session, candidates: Tuple[str, ...]) -> Optional[str]:
    d = _dialect(db)
    try:
        if d == "postgresql":
            for t in candidates:
                # to_regclass retorna NULL se não existe
                r = db.execute(text("select to_regclass(:n)"), {"n": f"public.{t}"}).scalar()
                if r:
                    return t
            return None

        if d == "sqlite":
            for t in candidates:
                r = db.execute(
                    text("select name from sqlite_master where type='table' and name=:n"),
                    {"n": t},
                ).scalar()
                if r:
                    return t
            return None
    except Exception:
        return None

    # fallback genérico (não garante)
    return None


def _get_cols(db: Session, table: str) -> List[str]:
    d = _dialect(db)
    cols: List[str] = []
    try:
        if d == "postgresql":
            rows = db.execute(
                text(
                    """
                    select column_name
                    from information_schema.columns
                    where table_schema='public' and table_name=:t
                    """
                ),
                {"t": table},
            ).all()
            cols = [r[0] for r in rows if r and r[0]]

        elif d == "sqlite":
            rows = db.execute(text(f"pragma table_info({table})")).all()
            # pragma table_info: cid, name, type, notnull, dflt_value, pk
            cols = [r[1] for r in rows if r and len(r) > 1]
    except Exception:
        cols = []
    return cols


def _pick_col(cols: List[str], candidates: Tuple[str, ...]) -> Optional[str]:
    cset = set(cols)
    for name in candidates:
        if name in cset:
            return name
    return None


def _order_clause(cols: List[str], dialect: str) -> str:
    # tenta ordenar por data, senão por id
    date_col = _pick_col(cols, ("created_at", "timestamp", "created", "date", "dia", "data"))
    id_col = _pick_col(cols, ("id", "tx_id", "ledger_id"))
    if date_col and id_col:
        if dialect == "postgresql":
            return f'"{date_col}" desc nulls last, "{id_col}" desc'
        return f'"{date_col}" desc, "{id_col}" desc'
    if date_col:
        if dialect == "postgresql":
            return f'"{date_col}" desc nulls last'
        return f'"{date_col}" desc'
    if id_col:
        return f'"{id_col}" desc'
    return "1"


def _ledger_fetch(
    db: Session,
    table: str,
    user_id: int,
    limit: int,
    offset: int,
) -> Tuple[List[Dict[str, Any]], str]:
    d = _dialect(db)
    cols = _get_cols(db, table)

    order_by = _order_clause(cols, d)

    # tabela é escolhida de uma allowlist, então ok usar f-string aqui
    sql = text(
        f"""
        select *
        from "{table}"
        where user_id = :uid
        order by {order_by}
        limit :lim offset :off
        """
    )

    rows = db.execute(sql, {"uid": int(user_id), "lim": int(limit), "off": int(offset)}).mappings().all()
    return [dict(r) for r in rows], d


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
    # compat com front antigo
    items: Optional[List[PixHistoryItem]] = None

    updated_at: str = Field(..., description="ISO8601 UTC")
    source: str = Field(default="real")


def _dt_to_iso(dt: Any) -> Optional[str]:
    if dt is None:
        return None
    try:
        if hasattr(dt, "isoformat"):
            return dt.isoformat()
        return str(dt)
    except Exception:
        return str(dt)


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ✅ permite admin + customer
):
    user_id = getattr(current_user, "id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token ausente.")

    # 1) tenta PixTransaction (se existir dado)
    q = db.query(PixTransaction).filter(PixTransaction.user_id == int(user_id))

    # ordenação tolerante
    cols_tx = set(PixTransaction.__table__.columns.keys())
    date_col_name = None
    for c in ("created_at", "timestamp", "created", "date", "dia", "data"):
        if c in cols_tx:
            date_col_name = c
            break
    if date_col_name:
        q = q.order_by(getattr(PixTransaction, date_col_name).desc())
    else:
        q = q.order_by(PixTransaction.id.desc())

    transactions = q.offset(offset).limit(limit).all()

    dias_map: Dict[str, Dict[str, float]] = {}
    history_items: List[Dict[str, Any]] = []

    def _accumulate(dia: str, tipo: str, valor: float):
        if dia not in dias_map:
            dias_map[dia] = {"entradas": 0.0, "saidas": 0.0}
        if tipo in ("recebimento", "entrada", "recebido"):
            dias_map[dia]["entradas"] += valor
        else:
            dias_map[dia]["saidas"] += valor

    if transactions:
        for t in transactions:
            dt = None
            if date_col_name:
                dt = getattr(t, date_col_name, None)
            dt = dt or getattr(t, "timestamp", None) or getattr(t, "created_at", None)
            dia = dt.strftime("%Y-%m-%d") if dt and hasattr(dt, "strftime") else "sem-data"

            tipo = str(getattr(t, "tipo", "") or "").lower()
            valor = _sf(getattr(t, "valor", 0.0) or 0.0)
            _accumulate(dia, tipo, valor)

            history_items.append(
                {
                    "user_id": getattr(t, "user_id", None),
                    "id": int(getattr(t, "id", 0) or 0),
                    "tipo": str(getattr(t, "tipo", "") or ""),
                    "valor": valor,
                    "taxa_percentual": float(getattr(t, "taxa_percentual", 0.0) or 0.0)
                    if hasattr(t, "taxa_percentual")
                    else None,
                    "taxa_valor": float(getattr(t, "taxa_valor", 0.0) or 0.0)
                    if hasattr(t, "taxa_valor")
                    else None,
                    "timestamp": _dt_to_iso(dt),
                    "descricao": getattr(t, "descricao", None),
                    "valor_liquido": float(getattr(t, "valor_liquido", getattr(t, "valor", 0.0)) or 0.0)
                    if hasattr(t, "valor_liquido")
                    else None,
                }
            )

        source = "real"

    else:
        # 2) fallback: ledger (pix_ledger / pix_ledger_main)
        ledger_tbl = _pick_table(db, ("pix_ledger", "pix_ledger_main"))
        if ledger_tbl:
            rows, d = _ledger_fetch(db, ledger_tbl, int(user_id), limit, offset)
            cols = _get_cols(db, ledger_tbl)

            id_col = _pick_col(cols, ("id", "tx_id", "ledger_id"))
            tipo_col = _pick_col(cols, ("tipo", "kind", "type", "direction"))
            valor_col = _pick_col(cols, ("amount", "valor", "value", "valor_bruto"))
            fee_val_col = _pick_col(cols, ("fee_amount", "taxa_valor", "fee", "fee_value"))
            fee_pct_col = _pick_col(cols, ("fee_percent", "taxa_percentual", "fee_pct", "fee_percentage"))
            desc_col = _pick_col(cols, ("descricao", "description", "memo", "note"))
            ts_col = _pick_col(cols, ("created_at", "timestamp", "created", "date", "dia", "data"))

            for i, r in enumerate(rows):
                dt = r.get(ts_col) if ts_col else None
                dia = "sem-data"
                try:
                    if dt and hasattr(dt, "strftime"):
                        dia = dt.strftime("%Y-%m-%d")
                    elif dt:
                        dia = str(dt)[:10]
                except Exception:
                    dia = "sem-data"

                raw_tipo = str(r.get(tipo_col, "") or "").lower() if tipo_col else ""
                raw_valor = _sf(r.get(valor_col, 0.0) if valor_col else 0.0)
                # se não tem tipo, tenta inferir pelo sinal
                if not raw_tipo:
                    raw_tipo = "entrada" if raw_valor >= 0 else "saida"

                valor_abs = abs(raw_valor)
                _accumulate(dia, raw_tipo, valor_abs)

                fee_val = _sf(r.get(fee_val_col, 0.0)) if fee_val_col else None
                fee_pct = _sf(r.get(fee_pct_col, 0.0)) if fee_pct_col else None
                valor_liq = None
                if fee_val is not None:
                    valor_liq = max(0.0, valor_abs - fee_val)

                history_items.append(
                    {
                        "user_id": int(user_id),
                        "id": int(r.get(id_col) or (i + 1)) if id_col else (i + 1),
                        "tipo": raw_tipo,
                        "valor": valor_abs,
                        "taxa_percentual": fee_pct if fee_pct_col else None,
                        "taxa_valor": fee_val if fee_val_col else None,
                        "timestamp": _dt_to_iso(dt),
                        "descricao": r.get(desc_col) if desc_col else None,
                        "valor_liquido": valor_liq,
                    }
                )

            source = "real"
        else:
            source = "lab"

    dias_out = [
        {"dia": k, "entradas": _sf(v["entradas"]), "saidas": _sf(v["saidas"])}
        for k, v in dias_map.items()
    ]

    # ✅ sempre retorna listas (nunca null)
    return {
        "dias": (dias_out or []),
        "history": (history_items or []),
        "items": (history_items or []),  # compat
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "real",
    }
