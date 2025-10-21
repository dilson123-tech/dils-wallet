from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from datetime import datetime

router = APIRouter(tags=["PIX"])

@router.get("/balance")
def get_balance(db: Session = Depends(get_db)):
    # mock temporário de saldo
    return {
        "balance": 1520.75,
        "entradas": 3500.00,
        "saidas": 1979.25,
    }

@router.get("/history")
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    now = datetime.utcnow().isoformat()
    items = [
        {
            "id": f"tx-{i}",
            "when": now,
            "type": "IN" if i % 2 == 0 else "OUT",
            "description": "PIX de teste automático",
            "value": 100.0 if i % 2 == 0 else -50.0
        }
        for i in range(limit)
    ]
    return {"items": items}
