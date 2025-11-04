from decimal import Decimal
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# Dependência de DB (se existir; caso não, o import falha silencioso)
try:
    from sqlalchemy.orm import Session
    from app.deps import get_db  # sua dependência padrão
except Exception:  # fallback se deps/SQLAlchemy não estiverem prontos
    Session = object  # dummy
    def get_db():
        return None

router = APIRouter()

@router.get("/balance")
def get_balance(db: Session = Depends(get_db), user_id: int = 1):
    """
    Endpoint resiliente: em qualquer erro, retorna saldo 0.0 (200).
    """
    try:
        # TODO: substituir por cálculo real usando o DB quando quisermos
        saldo_pix: Decimal | float = Decimal("0")
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
    """
    Endpoint resiliente: em qualquer erro, retorna lista vazia (200).
    """
    try:
        # TODO: substituir por query real quando os models/DB estiverem redondos
        history = []
        return JSONResponse(
            content=jsonable_encoder({"history": history}, custom_encoder={Decimal: float})
        )
    except Exception as e:
        print("[AUREA PIX] fallback /history:", e)
        return JSONResponse(
            content=jsonable_encoder({"history": []}, custom_encoder={Decimal: float})
        )
