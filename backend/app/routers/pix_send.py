from app.utils.pix_tx import create_pix_tx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models.idempotency import IdempotencyKey

# tentamos importar o user principal; se não existir, tratamos
try:
    from app.models.user_main import User as UserMain
except Exception:
    UserMain = None  # fallback

router = APIRouter(prefix="/pix", tags=["pix"])

class PixSendIn(BaseModel):
    valor: float = Field(..., gt=0, description="Valor em BRL, positivo")
    dest: str = Field(..., min_length=1, max_length=120, description="Identificação do destinatário")

@router.post("/send")
def pix_send(request: Request, payload: PixSendIn, db: Session = Depends(get_db)):
    from fastapi import Request
    sender_email = request.headers.get("X-User-Email") or "dilsonpereira231@gmail.com"
    try:
        sender = get_or_create_user(db, email=sender_email, name="Cliente Aurea Gold")
    # --- PIX fast-path: defaults e retorno imediato ---
    _valor = float(getattr(payload, "valor", 0) or 0)
    if _valor <= 0:
        raise HTTPException(status_code=400, detail="valor_invalido")
    _descricao = getattr(payload, "msg", None)
    try:
        _tx_id = create_pix_tx(db, user_id=getattr(sender, "id"), valor=_valor, descricao=_descricao, tipo="envio")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"pix_tx_failed: {e}")
    return {"status":"ok","pix_id": _tx_id, "valor": _valor, "descricao": _descricao, "tipo":"envio"}
    # --- fim fast-path ---

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"user_bootstrap_failed: {e}")
    """
    Cria uma transação PIX de saída (tipo='OUT').
    **Idempotência**: se houver `Idempotency-Key`, retorna a mesma resposta do primeiro POST.
    """
    key = request.headers.get("Idempotency-Key")
    if key:
        rec = db.query(IdempotencyKey).filter_by(key=key).first()
        if rec:
            try:
                data = json.loads(rec.response_json or "{}")
            except Exception:
                data = {}
            return JSONResponse(data, status_code=rec.status_code or 200)

    try:
        tx = PixTransaction(valor=payload.valor, tipo="OUT")

        if hasattr(PixTransaction, "timestamp"):
            setattr(tx, "timestamp", datetime.now(timezone.utc))
        if hasattr(PixTransaction, "descricao"):
            setattr(tx, "descricao", f"PIX para {payload.dest}")
        if hasattr(PixTransaction, "dest"):
            setattr(tx, "dest", payload.dest)
        if hasattr(PixTransaction, "user_id"):
            uid = None
            if UserMain is not None:
                u = db.query(UserMain).first()
                uid = getattr(u, "id", None) if u else None
            if uid is None:
                raise HTTPException(status_code=400, detail="pix_send_error: nenhum usuário cadastrado para vincular (user_id).")
            setattr(tx, "user_id", uid)

        db.add(tx)
        db.commit()
        db.refresh(tx)

        resp = {
            "id": getattr(tx, "id", None),
            "valor": float(getattr(tx, "valor", payload.valor)),
            "tipo": getattr(tx, "tipo", "OUT"),
            "timestamp": getattr(tx, "timestamp", None).isoformat() if getattr(tx, "timestamp", None) else None,
            "dest": payload.dest,
            "status": "OK",
        }

        # salva idempotência, se houver chave
        if key:
            try:
                db.add(IdempotencyKey(key=key, status_code=200, response_json=json.dumps(resp)))
                db.commit()
            except Exception:
                db.rollback()
                # segue sem quebrar

        return resp

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"pix_send_error: {e}")

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
from app.utils.users import get_or_create_user
