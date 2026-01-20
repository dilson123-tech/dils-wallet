from decimal import Decimal
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

try:
    from sqlalchemy.orm import Session
    from app.deps import get_db
    from app.services.pix_service import calcular_saldo, listar_historico
except Exception:
    Session = object
    def get_db(): return None
    def calcular_saldo(db, user_id): return Decimal(0)
    def listar_historico(db, user_id, limit=50): return []


from sqlalchemy import text
import json, base64
from typing import Optional

def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _jwt_sub_unverified(token: str) -> Optional[str]:
    # DEV: pega 'sub' sem validar assinatura
    try:
        _h, p, _s = token.split('.', 2)
    except ValueError:
        return None
    try:
        payload = json.loads(_b64url_decode(p).decode('utf-8'))
    except Exception:
        return None
    return payload.get('sub')

def _resolve_user_id(db, request, x_user_email: Optional[str]):
    auth = request.headers.get('authorization') or request.headers.get('Authorization')
    if auth and auth.lower().startswith('bearer '):
        sub = _jwt_sub_unverified(auth.split(' ',1)[1].strip())
        if sub:
            row = db.execute(text('SELECT id FROM users WHERE username=:u LIMIT 1'), {'u': sub}).fetchone()
            if row:
                return int(row[0])
    if x_user_email:
        row = db.execute(text('SELECT id FROM users WHERE email=:e LIMIT 1'), {'e': x_user_email}).fetchone()
        if row:
            return int(row[0])
    return None
router = APIRouter()

@router.get("/balance")
def get_balance(db: Session = Depends(get_db), user_id: int = 1):
    try:
        saldo_pix: Decimal = calcular_saldo(db, user_id)
        return JSONResponse(
            content=jsonable_encoder({"saldo_pix": saldo_pix}, custom_encoder={Decimal: float})
        )
    except Exception as e:
        print("[AUREA PIX] fallback /balance:", e)
        return JSONResponse(
            content=jsonable_encoder({"saldo_pix": 0.0}, custom_encoder={Decimal: float})
        )

@router.get("/history")
def get_history(db: Session = Depends(get_db), user_id: int = 1, limit: int = 50):
    try:
        history = listar_historico(db, user_id, limit)
        return JSONResponse(
            content=jsonable_encoder({"history": history}, custom_encoder={Decimal: float})
        )
    except Exception as e:
        print("[AUREA PIX] fallback /history:", e)
        return JSONResponse(
            content=jsonable_encoder({"history": []}, custom_encoder={Decimal: float})
        )
