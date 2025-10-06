from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.deps import get_db
from backend.app.models.pix_transaction import PixTransaction

router = APIRouter(prefix="/api/v1/pix", tags=["pix-stats"])

@router.get("/stats")
def get_pix_stats(db: Session = Depends(get_db)):
    """
    Retorna estatísticas globais do PIX:
    - total de transações
    - soma total transferida
    - valor médio
    - menor e maior transferência
    - data/hora da última transação
    """
    q = db.query(
        func.count(PixTransaction.id).label("total_count"),
        func.sum(PixTransaction.amount).label("total_amount"),
        func.avg(PixTransaction.amount).label("avg_amount"),
        func.min(PixTransaction.amount).label("min_amount"),
        func.max(PixTransaction.amount).label("max_amount"),
        func.max(PixTransaction.created_at).label("last_tx")
    ).first()

    return {
        "total_count": int(q.total_count or 0),
        "total_amount": float(q.total_amount or 0),
        "avg_amount": float(q.avg_amount or 0),
        "min_amount": float(q.min_amount or 0),
        "max_amount": float(q.max_amount or 0),
        "last_tx": str(q.last_tx) if q.last_tx else None
    }
