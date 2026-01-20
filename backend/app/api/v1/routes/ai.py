from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db

# Modelos podem variar; tratamos campos ausentes com getattr(...)
try:
    from app.models.pix_transaction import PixTransaction  # id, user_id, tipo, valor, descricao, created_at
except Exception:
    PixTransaction = None  # fallback para não quebrar import em fase de build

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

def _rows_to_dicts(rows: List[Any]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        out.append({
            "id": getattr(r, "id", None),
            "tipo": getattr(r, "tipo", None),
            "valor": float(getattr(r, "valor", 0) or 0),
            "descricao": getattr(r, "descricao", "") or "",
            "created_at": (
                getattr(r, "created_at", None).isoformat()
                if hasattr(r, "created_at") and isinstance(getattr(r, "created_at"), datetime)
                else getattr(r, "created_at", None)
            ),
            "user_id": getattr(r, "user_id", None),
        })
    return out

def _is_envio(tipo: Optional[str]) -> bool:
    if not tipo: return False
    t = tipo.lower()
    return t in ("envio", "send", "debito", "saída", "saida")

def _is_receb(tipo: Optional[str]) -> bool:
    if not tipo: return False
    t = tipo.lower()
    # no teu histórico as entradas apareceram como "PIX"
    return t in ("pix", "recebimento", "credito", "entrada", "in")

@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
    limit: int = 50,
):
    """
    Resposta padronizada para o front:

    {
      "total_envios": number,
      "total_transacoes": number,
      "recebimentos": number,
      "entradas": number,
      "saldo_estimado": number,
      "txs": [{ id, tipo, valor, descricao, created_at }]
    }
    """
    if PixTransaction is None:
        # ambiente sem modelos carregados: responde vazio, mas padronizado
        return {
            "total_envios": 0.0,
            "total_transacoes": 0,
            "recebimentos": 0.0,
            "entradas": 0,
            "saldo_estimado": 0.0,
            "txs": [],
        }

    q = db.query(PixTransaction)
    # Se você filtra por usuário por e-mail em outra tabela, dá pra adaptar aqui.
    # Por ora retorna geral. (Se quiser, depois mapeamos X-User-Email -> user_id.)

    # últimas transações (mais recentes primeiro)
    q = q.order_by(PixTransaction.id.desc()).limit(limit)
    rows = q.all() or []
    txs = _rows_to_dicts(rows)

    total_envios = sum(t["valor"] for t in txs if _is_envio(t.get("tipo")))
    recebimentos = sum(t["valor"] for t in txs if _is_receb(t.get("tipo")))
    entradas = sum(1 for t in txs if _is_receb(t.get("tipo")))
    total_transacoes = len(txs)
    saldo_estimado = recebimentos - total_envios

    return {
        "total_envios": round(total_envios, 2),
        "total_transacoes": int(total_transacoes),
        "recebimentos": round(recebimentos, 2),
        "entradas": int(entradas),
        "saldo_estimado": round(saldo_estimado, 2),
        "txs": txs[:10],  # o front usa só as 10 últimas
    }
