from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction

# user model opcional
try:
    from app.models.user_main import User as UserMain
except Exception:
    UserMain = None

router = APIRouter()

class PixSendIn(BaseModel):
    dest: str = Field(..., description="destinatário (email/chave pix)")
    valor: float = Field(..., gt=0, description="valor do pix (R$)")
    msg: str | None = None
    descricao: str | None = None

def _get_user_email(request: Request, x_user_email: str | None) -> str | None:
    """
    Tenta extrair o e-mail do usuário de várias formas de header:
    X-User-Email / x-user-email / X_User_Email / x_user_email
    """
    if x_user_email:
        return x_user_email
    for k in ("x-user-email", "X-User-Email", "x_user_email", "X_User_Email"):
        v = request.headers.get(k)
        if v:
            return v
    return None

def _ensure_user_id(db: Session, email: str | None) -> int:
    if not UserMain:
        raise HTTPException(status_code=400, detail="user_table_missing: tabela de usuários indisponível")
    if not email:
        raise HTTPException(status_code=400, detail="missing_header:X-User-Email")
    u = db.query(UserMain).filter(UserMain.email == email).first()
    if not u:
        # cria usuário mínimo para satisfazer FK
        name = email.split("@")[0] if "@" in email else email
        try:
            u = UserMain(email=email, name=name)  # se o modelo não tiver name, o SQLAlchemy ignora
        except TypeError:
            u = UserMain(email=email)
        db.add(u)
        db.commit()
        db.refresh(u)
    return int(u.id)

@router.post("/pix/send")
def pix_send(
    payload: PixSendIn,
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email", convert_underscores=False),
):
    desc = (payload.msg or payload.descricao or "").strip() or "PIX"
    try:
        user_email = _get_user_email(request, x_user_email)
        uid = _ensure_user_id(db, user_email)
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

@router.get("/pix/list")
def pix_list(
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email", convert_underscores=False),
):
    try:
        user_email = _get_user_email(request, x_user_email)
        uid = _ensure_user_id(db, user_email)
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
