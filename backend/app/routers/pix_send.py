from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction

# tentamos importar o user principal; se não existir, tratamos
try:
    from app.models.user_main import User as UserMain
except Exception:
    UserMain = None  # fallback

router = APIRouter()

class PixSendIn(BaseModel):
    dest: str = Field(..., description="destinatário (email/chave pix)")
    valor: float = Field(..., gt=0, description="valor do pix (R$)")
    # aceitamos msg ou descricao; ambas opcionais, mas nunca salvaremos nulo
    msg: str | None = None
    descricao: str | None = None

def _resolve_user_id(db: Session, email: str | None) -> int:
    if email and UserMain:
        u = db.query(UserMain).filter(UserMain.email == email).first()
        if u:
            return int(u.id)
    # fallback simples para ambiente sem tabela de usuários
    return 1

@router.post("/pix/send")
def pix_send(payload: PixSendIn,
             db: Session = Depends(get_db),
             x_user_email: str | None = Header(default=None, convert_underscores=False)):
    # normaliza descrição: nunca None, nunca vazia
    desc = (payload.msg or payload.descricao or "").strip() or "PIX"
    try:
        tx = PixTransaction(
            user_id=_resolve_user_id(db, x_user_email),
            tipo="envio",
            valor=float(payload.valor),
            descricao=desc
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return JSONResponse({"ok": True, "id": tx.id, "descricao": tx.descricao})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"pix_tx_failed: {e}")
