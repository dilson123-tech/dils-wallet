from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction



from sqlalchemy import text
import json, base64
from typing import Optional
import math
import os

def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _jwt_sub_unverified(token: str) -> Optional[str]:
    # DEV: pega 'sub' sem validar assinatura
    try:
        _h, p, _s = token.split('.', 2)
        payload = json.loads(_b64url_decode(p).decode('utf-8'))
        return payload.get('sub')
    except Exception:
        return None

def _resolve_user_id(db, request, x_user_email: Optional[str]):
    auth = request.headers.get('authorization') or request.headers.get('Authorization')
    if auth and auth.lower().startswith('bearer '):
        sub = _jwt_sub_unverified(auth.split(' ',1)[1].strip())
        if sub:
            row = db.execute(text('SELECT id FROM users WHERE username=:u OR email=:u LIMIT 1'), {'u': sub}).fetchone()
            if row:
                return int(row[0])
    if x_user_email:
        row = db.execute(text('SELECT id FROM users WHERE email=:e OR username=:e LIMIT 1'), {'e': x_user_email}).fetchone()
        if row:
            return int(row[0])
    return None
router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

# TODO: ligar com auth/JWT e X-User-Email de verdade.
USER_FIXO_ID = 1


@router.get("/balance")
def get_pix_balance(request: Request, x_user_email: str = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
    debug: int = 0,
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
    debug_tx_total = None
    debug_tipos = []
    debug_user_id = None

    def _sf(x: float) -> float:
        try:
            v = float(x)
            return v if math.isfinite(v) else 0.0
        except Exception:
            return 0.0

    # resolve usuário real (Bearer sub ou X-User-Email). fallback: USER_FIXO_ID
    user_id = _resolve_user_id(db, request, x_user_email)
    if not user_id:
        user_id = USER_FIXO_ID
        debug_error = (debug_error or "") + "|user_fallback"
    debug_user_id = user_id

    try:
        debug_tx_total = int(db.query(func.count(PixTransaction.id)).filter(PixTransaction.user_id == user_id).scalar() or 0)
        debug_tipos = [r[0] for r in db.query(PixTransaction.tipo).filter(PixTransaction.user_id == user_id).distinct().all()][:12]
    except Exception as _e:
        debug_tx_total = None
        debug_tipos = []
        debug_error = (debug_error or "") + f"|debug:{_e}"

    try:
        # Entradas: PIX recebidos (e qualquer tipo marcado como 'entrada')
        entradas = _sf(
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
            .filter(
                PixTransaction.user_id == user_id,
                PixTransaction.tipo.in_(["recebimento", "entrada"]),
            )
            .scalar()
        )

        # Saídas: PIX enviados (e qualquer tipo marcado como 'saida')
        saidas = _sf(
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
            .filter(
                PixTransaction.user_id == user_id,
                PixTransaction.tipo.in_(["envio", "saida"]),
            )
            .scalar()
        )

        saldo = _sf(entradas - saidas)

        # --- últimos 7 dias (agregado por dia) ---
        hoje = date.today()
        day_map = {}
        for i in range(6, -1, -1):
            d = hoje - timedelta(days=i)
            k = d.isoformat()
            day_map[k] = {"dia": k, "entradas": 0.0, "saidas": 0.0, "saldo_dia": 0.0}
        # ultimos_7d: tolerante a timestamp NULL (usa últimas tx por id)
        rows = (
            db.query(PixTransaction)
            .filter(PixTransaction.user_id == user_id)
            .order_by(PixTransaction.id.desc())
            .limit(500)
            .all()
        )
        for tx in rows:
            # se timestamp faltando/nulo, cai para dia de hoje
            dt = getattr(tx, 'timestamp', None) or datetime.combine(hoje, datetime.min.time())
            try:
                dia = dt.date().isoformat()
            except Exception:
                try:
                    dia = datetime.fromisoformat(str(dt)).date().isoformat()
                except Exception:
                    continue
            if dia not in day_map:
                continue
            v = _sf(getattr(tx, 'valor', 0.0) or 0.0)
            tipo = str(getattr(tx, 'tipo', '') or '').lower()
            if tipo in ('recebimento','entrada'):
                day_map[dia]['entradas'] += v
            elif tipo in ('envio','saida'):
                day_map[dia]['saidas'] += v
        for k in list(day_map.keys()):
            day_map[k]["entradas"] = _sf(day_map[k]["entradas"])
            day_map[k]["saidas"] = _sf(day_map[k]["saidas"])
            day_map[k]["saldo_dia"] = _sf(day_map[k]["entradas"] - day_map[k]["saidas"])
        ultimos_7d = list(day_map.values()) if day_map else []

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

    # ✅ Payload "limpo" (produção): sem debug_* por padrão
    payload = {
        "saldo": _sf(saldo),
        "source": source,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        # Campos antigos mantidos para compatibilidade com IA 3.0:
        "saldo_atual": _sf(saldo),
        "entradas_mes": _sf(entradas),
        "saidas_mes": _sf(saidas),
        "ultimos_7d": ultimos_7d,
    }

    # 🔍 Debug só quando explicitamente ligado (AUREA_DEBUG=1) + ?debug=1
    allow_debug = os.getenv("AUREA_DEBUG", "").strip().lower() in ("1", "true", "yes", "on")
    if allow_debug and int(debug or 0) == 1:
        payload.update({
            "debug_error": debug_error,
            "debug_user_id": user_id,
            "debug_tx_total": debug_tx_total,
            "debug_tipos": debug_tipos,
        })

    return payload
