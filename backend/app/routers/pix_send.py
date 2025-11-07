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
    # -- normaliza payload (Pydantic v1/v2) p/ dict --
    try:
        data = payload.model_dump()
    except AttributeError:
        try:
            data = payload.dict()
        except Exception:
            data = dict(payload)
    # descricao: cai para msg ou vazio se vier None
    descricao = (data.get("descricao") or data.get("msg") or "")
    data["descricao"] = descricao
    if not (data.get("descricao") or ""):
        payload["descricao"] = payload.get("msg", "") or "PIX sem descrição"
    # Identidade do remetente (fallback padrão)
    sender_email = request.headers.get("X-User-Email") or "dilsonpereira231@gmail.com"

    # Garante que existe um usuário para vincular a transação
    try:
        sender = get_or_create_user(db, email=sender_email, name="Cliente Aurea Gold")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"user_bootstrap_failed: {e}")

    # Validação e criação rápida da transação PIX
    _valor = float(payload.valor or 0)
    if _valor <= 0:
        raise HTTPException(status_code=400, detail="valor_invalido")

    _descricao = getattr(payload, "msg", None)

    try:
        _tx_id = create_pix_tx(
            db,
            user_id=getattr(sender, "id", None),
            valor=_valor,
            descricao=_descricao,
            tipo="envio",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"pix_tx_failed: {e}")

    return {"status": "ok", "pix_id": _tx_id, "valor": _valor, "descricao": _descricao, "tipo": "envio"}

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
