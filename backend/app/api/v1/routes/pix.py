from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.config import settings
from datetime import datetime, timedelta

router = APIRouter(tags=["PIX"])

def _demo_balance():
    # valores de exemplo só pra UI
    entradas = 1250.40
    saidas = 800.10
    return {
        "balance": round(entradas - saidas, 2),
        "in_total": entradas,
        "out_total": saidas,
        "result": round(entradas - saidas, 2),
    }

def _demo_history(limit: int):
    base = datetime.utcnow()
    items = []
    for i in range(limit):
        dt = base - timedelta(hours=i*6)
        items.append({
            "id": f"demo-{i+1}",
            "when": dt.isoformat() + "Z",
            "type": "IN" if i % 2 == 0 else "OUT",
            "description": "PIX recebido" if i % 2 == 0 else "PIX enviado",
            "amount": 150.0 if i % 2 == 0 else 90.0
        })
    return items

@router.get("/balance")
def get_balance(db: Session = Depends(get_db)):
    if settings.AUREA_DEMO:
        return _demo_balance()
    # TODO: Implementar saldo real usando o banco
    return {"balance": 0.0, "in_total": 0.0, "out_total": 0.0, "result": 0.0}

@router.get("/history")
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    if settings.AUREA_DEMO:
        return {"items": _demo_history(limit)}
    # TODO: Implementar consulta real no banco
    return {"items": []}
