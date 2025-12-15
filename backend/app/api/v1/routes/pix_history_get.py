from fastapi import APIRouter, Depends, Query, Header, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.pix_transaction import PixTransaction
from sqlalchemy import text
import os, json, base64, hmac, hashlib
from typing import Optional

def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _jwt_sub_verified(token: str) -> Optional[str]:
    """DEV MODE: extrai 'sub' do JWT SEM validar assinatura."""
    try:
        _h_b64, p_b64, _s_b64 = token.split(".", 2)
    except ValueError:
        return None
    try:
        payload = json.loads(_b64url_decode(p_b64).decode("utf-8"))
    except Exception:
        return None
    return payload.get("sub")

def _resolve_user_id(db, request, x_user_email: Optional[str]):
    # 1) Bearer token -> users.username (sub) -> users.id
    auth = request.headers.get('authorization') or request.headers.get('Authorization')
    if auth and auth.lower().startswith('bearer '):
        token = auth.split(' ', 1)[1].strip()
        sub = _jwt_sub_verified(token)
        if sub:
            row = db.execute(text('SELECT id FROM users WHERE username=:u LIMIT 1'), {'u': sub}).fetchone()
            if row:
                return int(row[0])

    # 2) fallback compat: X-User-Email -> users.id
    if x_user_email:
        row = db.execute(text('SELECT id FROM users WHERE email=:e LIMIT 1'), {'e': x_user_email}).fetchone()
        if row:
            return int(row[0])

    return None


router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])

def _pick_date_col():
    candidates = ["created_at", "created", "timestamp", "data", "dia", "date"]
    cols = set(PixTransaction.__table__.columns.keys())
    for name in candidates:
        if name in cols:
            return getattr(PixTransaction, name)
    return None

DATE_COL = _pick_date_col()

@router.get("/history")
def get_pix_history(request: Request, 
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    q = db.query(PixTransaction)

    user_id = _resolve_user_id(db, request, x_user_email)

    # ✅ Prioridade: user_id (token) -> email (fallback)
    if user_id and 'user_id' in PixTransaction.__table__.columns.keys():
        q = q.filter(PixTransaction.user_id == user_id)
    elif x_user_email and 'email' in PixTransaction.__table__.columns.keys():
        q = q.filter(PixTransaction.email == x_user_email)

    if DATE_COL is not None:
        q = q.order_by(DATE_COL.desc())

    transactions = q.offset(offset).limit(limit).all()

    dias_map = {}
    for t in transactions:
        dt = getattr(t, DATE_COL.key) if DATE_COL is not None else getattr(t, "dia", None) or getattr(t, "data", None)
        dia = dt.strftime("%Y-%m-%d") if dt else "sem-data"

        if dia not in dias_map:
            dias_map[dia] = {"dia": dia, "entradas": 0.0, "saidas": 0.0}

        if getattr(t, "tipo", "") == "recebido":
            dias_map[dia]["entradas"] += float(getattr(t, "valor", 0) or 0)
        else:
            dias_map[dia]["saidas"] += float(getattr(t, "valor", 0) or 0)

    return {"dias": list(dias_map.values()), "history": transactions}
