from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.schemas.pix_transaction_schema import PixTransactionResponse

router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])

@router.get("/history", response_model=list[PixTransactionResponse])
def get_pix_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retorna o histórico completo de transferências PIX mock."""
    transactions = (
        db.query(PixTransaction)
        .order_by(PixTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return transactions
