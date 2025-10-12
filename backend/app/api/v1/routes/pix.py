from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db

# sem prefixo aqui; o prefixo /api/v1/pix vem do main.py
router = APIRouter(tags=["PIX"])

@router.get("/balance")
def get_balance(db: Session = Depends(get_db)):
    # TODO: implementar saldo real no banco
    return {"balance": 0.0}

@router.get("/history")
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    # TODO: implementar consulta real no banco
    items = [
        {
            "id": f"mock-{i}",
            "when": "2025-10-11T19:00:00Z",
            "type": "IN" if i % 2 == 0 else "OUT",
            "description": "Transação teste",
            "amount": 100.0 - i,
        }
        for i in range(limit)
    ]
    return {"items": items}
