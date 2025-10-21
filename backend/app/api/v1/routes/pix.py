from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from datetime import datetime

router = APIRouter(prefix="/pix", tags=["PIX"])

@router.get("/balance")
def get_balance(db: Session = Depends(get_db)):
    return {"balance": 1500.75, "entradas": 3500.00, "saidas": 2000.25}

@router.get("/history")
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    now = datetime.utcnow().isoformat()
    items = [
        {"id": f"tx-{i}", "when": now, "type": "IN" if i % 2 == 0 else "OUT",
         "description": "Transferência de teste", "value": 150.50 if i % 2 == 0 else -80.30}
        for i in range(limit)
    ]
    return {"items": items}
