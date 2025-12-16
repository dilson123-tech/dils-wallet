from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction



from sqlalchemy import text
import json, base64
from typing import Optional

def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _jwt_sub_unverified(token: str) -> Optional[str]:
    # DEV: pega 'sub' sem validar assinatura
    try:

        user_id = _resolve_user_id(db, request, x_user_email) or USER_FIXO_ID
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
router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

# TODO: ligar com auth/JWT e X-User-Email de verdade.
USER_FIXO_ID = 1


@router.get("/balance")
def get_pix_balance(request: Request, x_user_email: str = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    """
    Versão GET da rota /api/v1/pix/balance.

    Por enquanto:
    - Ignora o e-mail e usa um usuário fixo (USER_FIXO_ID).
    - Calcula o saldo a partir das transações PixTransaction.
    - Devolve payload normalizado para painel e IA 3.0:

    {
      "saldo": number,
      "source": "lab" | "real",
      "updated_at": ISO8601,
      "saldo_atual": number,
      "entradas_mes": number,
      "saidas_mes": number,
      "debug_error": str | null
    }
    """
    debug_error = None

    try:
        # Entradas: PIX recebidos (e qualquer tipo marcado como 'entrada')
        entradas = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
            .filter(
                PixTransaction.user_id == user_id,
                PixTransaction.tipo.in_(["recebimento", "entrada"]),
            )
            .scalar()
            or 0.0
        )

        # Saídas: PIX enviados (e qualquer tipo marcado como 'saida')
        saidas = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
            .filter(
                PixTransaction.user_id == user_id,
                PixTransaction.tipo.in_(["envio", "saida"]),
            )
            .scalar()
            or 0.0
        )

        saldo = float(entradas - saidas)

        # --- últimos 7 dias (agregado por dia) ---
        hoje = date.today()
        day_map = {}
        for i in range(6, -1, -1):
            d = hoje - timedelta(days=i)
            k = d.isoformat()
            day_map[k] = {"dia": k, "entradas": 0.0, "saidas": 0.0, "saldo_dia": 0.0}

        ts_col = getattr(PixTransaction, "created_at", None)
        rows_q = db.query(PixTransaction).filter(PixTransaction.user_id == user_id)
        if ts_col is not None:
            start_dt = datetime.utcnow() - timedelta(days=7)
            rows_q = rows_q.filter(ts_col >= start_dt)
        rows = rows_q.all()

        for tx in rows:
            dt = getattr(tx, "created_at", None) or getattr(tx, "data", None) or getattr(tx, "timestamp", None)
            if not dt:
                continue
            try:
                dia = dt.date().isoformat()
            except Exception:
                continue
            if dia not in day_map:
                continue
            v = float(getattr(tx, "valor", 0.0) or 0.0)
            tipo = str(getattr(tx, "tipo", "") or "").lower()
            if tipo in ("recebimento", "entrada"):
                day_map[dia]["entradas"] += v
            elif tipo in ("envio", "saida"):
                day_map[dia]["saidas"] += v

        for k in list(day_map.keys()):
            day_map[k]["saldo_dia"] = float(day_map[k]["entradas"] - day_map[k]["saidas"])
        ultimos_7d = list(day_map.values())

        source = "real"
    except Exception as e:
        print("[AUREA PIX] erro em get_pix_balance:", e)
        debug_error = str(e)
        entradas = 0.0
        saidas = 0.0
        saldo = 0.0
        source = "lab"
        hoje = date.today()
        ultimos_7d = []
        for i in range(6, -1, -1):
            d = hoje - timedelta(days=i)
            ultimos_7d.append({"dia": d.isoformat(), "entradas": 0.0, "saidas": 0.0, "saldo_dia": 0.0})

    return {
        "saldo": float(saldo),
        "source": source,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        # Campos antigos mantidos para compatibilidade com IA 3.0:
        "saldo_atual": float(saldo),
        "entradas_mes": float(entradas),
        "saidas_mes": float(saidas),
        "ultimos_7d": ultimos_7d,
        # Só pra debugar por enquanto
        "debug_error": debug_error,
    }
