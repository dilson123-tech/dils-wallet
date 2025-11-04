from decimal import Decimal
from typing import List, Dict

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import func, case
    from app.models.pix_transaction import PixTransaction  # ajuste se o nome do model for outro
except Exception:
    # fallback se não tiver DB em dev
    Session = object
    def func(*a, **k): ...
    def case(*a, **k): ...
    class PixTransaction:  # type: ignore
        pass

def calcular_saldo(db: Session, user_id: int) -> Decimal:
    """Entradas - Saídas do usuário."""
    try:
        entrada = db.query(func.coalesce(func.sum(
            case((PixTransaction.tipo == 'entrada', PixTransaction.valor), else_=0)
        ), 0)).filter(PixTransaction.user_id == user_id).scalar() or 0
        saida = db.query(func.coalesce(func.sum(
            case((PixTransaction.tipo == 'saida', PixTransaction.valor), else_=0)
        ), 0)).filter(PixTransaction.user_id == user_id).scalar() or 0
        return Decimal(entrada) - Decimal(saida)
    except Exception as e:
        print("[AUREA PIX] calcular_saldo fallback:", e)
        return Decimal(0)

def listar_historico(db: Session, user_id: int, limit: int = 50) -> List[Dict]:
    """Últimas transações (mais recentes)."""
    try:
        q = (db.query(PixTransaction)
               .filter(PixTransaction.user_id == user_id)
               .order_by(PixTransaction.id.desc())
               .limit(limit))
        out: List[Dict] = []
        for t in q:
            out.append({
                "id": getattr(t, "id", None),
                "tipo": getattr(t, "tipo", None),
                "valor": getattr(t, "valor", 0),
                "descricao": getattr(t, "descricao", None),
                "timestamp": getattr(t, "timestamp", None),
            })
        return out
    except Exception as e:
        print("[AUREA PIX] listar_historico fallback:", e)
        return []
