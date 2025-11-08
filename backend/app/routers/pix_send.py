from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models.idempotency import IdempotencyKey  # mantido caso use depois
from app.utils.pix_tx import create_pix_tx
from app.utils.users import get_or_create_user

router = APIRouter(prefix="/pix", tags=["pix"])

class PixSendIn(BaseModel):
    valor: float = Field(..., gt=0, description="Valor em BRL, positivo")
    dest: str = Field(..., min_length=1, max_length=120, description="Identificação do destinatário")

@router.post("/send")
def pix_send(request: Request, payload: PixSendIn, db: Session = Depends(get_db)):
    """
    Envia PIX e SEMPRE responde JSON.
    - Normaliza payload (pydantic v1/v2)
    - Gera descricao_final com fallbacks
    - Garante usuário (fallback id=1 se não existir modelo)
    - Cria PixTransaction e retorna JSONResponse
    """
    try:
        # Normaliza payload -> dict
        try:
            data = payload.model_dump()
        except AttributeError:
            try:
                data = payload.dict()
            except Exception:
                data = dict(payload)

        # Descrição final (fallbacks) limitada
        descricao_final = str((
            data.get("descricao")
            or data.get("mensagem")
            or data.get("message")
            or data.get("msg")
            or "PIX"
        )).strip()[:140]

        # Remetente
        sender_email = request.headers.get("X-User-Email") or "dilsonpereira231@gmail.com"

        # Valor
        _valor = float(data.get("valor") or getattr(payload, "valor", 0) or 0)
        if _valor <= 0:
            return JSONResponse(status_code=400, content={"ok": False, "error": "valor_invalido"})

        # Garante usuário (se modelo existir); senão usa 1
        user_id = 1
        try:
            try:
                from app.models.user_main import User as UserMain
            except Exception:
                UserMain = None
            if UserMain is not None:
                user = db.query(UserMain).filter(UserMain.email == sender_email).first()
                if not user:
                    user = UserMain(email=sender_email, name="Cliente Aurea Gold")
                    db.add(user); db.commit(); db.refresh(user)
                user_id = int(user.id)
        except Exception:
            pass

        # Cria transação
        tx = PixTransaction(user_id=user_id, tipo="envio", valor=_valor, descricao=descricao_final)
        db.add(tx); db.commit(); db.refresh(tx)

        resp = {
            "ok": True,
            "id": getattr(tx, "id", None),
            "valor": float(getattr(tx, "valor", _valor)),
            "descricao": descricao_final,
            "service": "dils-wallet",
        }
        return JSONResponse(content=resp)

    except Exception as e:
        # NUNCA retorna texto puro; sempre JSON
        return JSONResponse(status_code=500, content={"ok": False, "error": f"pix_send_failed: {type(e).__name__}: {e}"})
@router.get("/list")
def pix_list(limit: int = 10, db: Session = Depends(get_db)):
    """Lista as últimas transações (default 10)."""
    try:
        q = db.query(PixTransaction)
        if hasattr(PixTransaction, "id"):
            q = q.order_by(getattr(PixTransaction, "id").desc())
        return [
            {
                "id": getattr(t, "id", None),
                "valor": float(getattr(t, "valor", 0.0)),
                "tipo": getattr(t, "tipo", None),
                "timestamp": getattr(t, "timestamp", None).isoformat() if getattr(t, "timestamp", None) else None,
            }
            for t in q.limit(limit).all()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pix_list_error: {e}")
