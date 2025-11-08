from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction

# user model opcional (projeto pode chamar diferente)
try:
    from app.models.user_main import User as UserMain
except Exception:
    UserMain = None  # se não existir, vamos exigir header e falhar de forma clara

router = APIRouter()

class PixSendIn(BaseModel):
    dest: str = Field(..., description="destinatário (email/chave pix)")
    valor: float = Field(..., gt=0, description="valor do pix (R$)")
    msg: str | None = None
    descricao: str | None = None

def _ensure_user_id(db: Session, email: str | None) -> int:
    if not UserMain:
        # Sem tabela de usuários, não temos como cumprir FK.
        # Melhor retornar 400 explícito do que estourar 500 de FK.
        raise HTTPException(status_code=400, detail="user_table_missing: tabela de usuários indisponível")

    if not email:
        raise HTTPException(status_code=400, detail="missing_header:X-User-Email")

    u = db.query(UserMain).filter(UserMain.email == email).first()
    if not u:
        # cria usuário mínimo para satisfazer FK
        u = UserMain(email=email, name=(email.split("@")[0] if hasattr(UserMain, "name") else None))
        db.add(u)
        db.commit()
        db.refresh(u)
    return int(u.id)

@router.post("/pix/send")
def pix_send(payload: PixSendIn,
             db: Session = Depends(get_db),
             x_user_email: str | None = Header(default=None, convert_underscores=False)):
    desc = (payload.msg or payload.descricao or "").strip() or "PIX"
    try:
        uid = _ensure_user_id(db, x_user_email)
        tx = PixTransaction(
            user_id=uid,
            tipo="envio",
            valor=float(payload.valor),
            descricao=desc
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return JSONResponse({"ok": True, "id": tx.id, "descricao": tx.descricao})
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"pix_tx_failed: {e}")

# Garantimos a rota /pix/list aqui também, para não depender de outro router
@router.get("/pix/list")
def pix_list(db: Session = Depends(get_db),
             x_user_email: str | None = Header(default=None, convert_underscores=False)):
    try:
        uid = _ensure_user_id(db, x_user_email)
        q = db.query(PixTransaction).filter(PixTransaction.user_id == uid).order_by(PixTransaction.id.desc()).all()
        out = []
        for t in q:
            out.append({
                "id": t.id,
                "tipo": t.tipo,
                "valor": float(t.valor),
                "descricao": t.descricao,
                "timestamp": getattr(t, "timestamp", None)
            })
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pix_list_failed: {e}")
