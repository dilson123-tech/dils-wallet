from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.pix_transaction import PixTransaction
from backend.app.schemas.pix_transaction_schema import PixTransactionResponse

router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])

@router.get("/history", response_model=list[PixTransactionResponse])
def get_pix_history(db: Session = Depends(get_db)):
    """Retorna o histórico completo de transferências PIX mock."""
    transactions = db.query(PixTransaction).order_by(PixTransaction.created_at.desc()).all()
    return transactions
