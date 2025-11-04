from decimal import Decimal
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

try:
    from sqlalchemy.orm import Session
    from app.deps import get_db
    from app.services.pix_service import calcular_saldo, listar_historico
except Exception:
    Session = object
    def get_db(): return None
    def calcular_saldo(db, user_id): return Decimal(0)
    def listar_historico(db, user_id, limit=50): return []

router = APIRouter()

@router.get("/balance")
def get_balance(db: Session = Depends(get_db), user_id: int = 1):
    try:
        saldo_pix: Decimal = calcular_saldo(db, user_id)
        return JSONResponse(
            content=jsonable_encoder({"saldo_pix": saldo_pix}, custom_encoder={Decimal: float})
        )
    except Exception as e:
        print("[AUREA PIX] fallback /balance:", e)
        return JSONResponse(
            content=jsonable_encoder({"saldo_pix": 0.0}, custom_encoder={Decimal: float})
        )

@router.get("/history")
def get_history(db: Session = Depends(get_db), user_id: int = 1, limit: int = 50):
    try:
        history = listar_historico(db, user_id, limit)
        return JSONResponse(
            content=jsonable_encoder({"history": history}, custom_encoder={Decimal: float})
        )
    except Exception as e:
        print("[AUREA PIX] fallback /history:", e)
        return JSONResponse(
            content=jsonable_encoder({"history": []}, custom_encoder={Decimal: float})
        )
