from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.pix_transaction import PixTransaction

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

def _is_receb(tipo: str) -> bool:
    t = (tipo or "").strip().lower()
    return t in ("pix", "recebimento", "credito", "entrada", "in")

def _is_envio(tipo: str) -> bool:
    t = (tipo or "").strip().lower()
    return not _is_receb(t)

@router.get("/summary")
def summary(limit: int = 50,
            x_user_email: Optional[str] = Header(default=None),
            db: Session = Depends(get_db)):
    # Busca transações mais recentes
    q = db.query(PixTransaction).order_by(PixTransaction.id.desc()).limit(limit)
    rows: List[PixTransaction] = q.all()

    # Totais
    total_envios = sum(float(r.valor) for r in rows if _is_envio(r.tipo))
    recebimentos = sum(float(r.valor) for r in rows if _is_receb(r.tipo))
    entradas = sum(1 for r in rows if _is_receb(r.tipo))
    total_transacoes = len(rows)
    saldo_estimado = recebimentos - total_envios

    # Lista normalizada (created_at mapeado de timestamp)
    txs = [{
        "id": r.id,
        "tipo": r.tipo,
        "valor": float(r.valor),
        "descricao": r.descricao,
        "created_at": (r.timestamp.isoformat() if getattr(r, "timestamp", None) else None),
        "user_id": r.user_id,
    } for r in rows]

    return {
        "total_envios": round(total_envios, 2),
        "total_transacoes": total_transacoes,
        "recebimentos": round(recebimentos, 2),
        "entradas": entradas,
        "saldo_estimado": round(saldo_estimado, 2),
        "txs": txs
    }
