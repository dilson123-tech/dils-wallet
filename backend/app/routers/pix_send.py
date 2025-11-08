from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction

# Modelo de usuário (pode variar por projeto)
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
    if x_user_email:
        return x_user_email
    for k in ("x-user-email", "X-User-Email", "x_user_email", "X_User_Email"):
        v = request.headers.get(k)
        if v:
            return v
    return None

def _ensure_user_id(db: Session, email_hint: str | None) -> int:
    """
    Retorna um user_id válido para satisfazer o FK, sem assumir nomes de colunas.
    Estratégia:
      1) Se existir qualquer usuário, usa o primeiro (estáveis/livres de schema).
      2) Se a tabela estiver vazia, tenta criar um usuário mínimo preenchendo
         apenas colunas disponíveis (name/username/user_email/email se existirem).
    """
    if not UserMain:
        raise HTTPException(status_code=400, detail="user_table_missing: tabela de usuários indisponível")

    # 1) Há usuário? Usa o primeiro.
    u = db.query(UserMain).first()
    if u:
        return int(getattr(u, "id"))

    # 2) Tabela vazia: criar usuário mínimo, preenchendo só o que existir.
    cols = {c.name for c in UserMain.__table__.columns}
    data = {}
    alias_email = email_hint or "seed@aurea.local"
    alias_name = (alias_email.split("@")[0] if "@" in alias_email else alias_email)

    for candidate, value in [
        ("email", alias_email),
        ("user_email", alias_email),
        ("username", alias_name),
        ("name", alias_name),
        ("login", alias_name),
    ]:
        if candidate in cols:
            data[candidate] = value

    try:
        u = UserMain(**data)  # se o modelo não tiver esses campos, data fica vazio
        db.add(u)
        db.commit()
        db.refresh(u)
        return int(getattr(u, "id"))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"user_seed_required: não foi possível criar usuário mínimo ({e}). Crie um usuário na tabela e tente novamente."
        )

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
        tx = PixTransaction(user_id=uid, tipo="envio", valor=float(payload.valor), descricao=desc)
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
        return [
            {
                "id": t.id,
                "tipo": t.tipo,
                "valor": float(t.valor),
                "descricao": t.descricao,
                "timestamp": getattr(t, "timestamp", None),
            }
            for t in q
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pix_list_failed: {e}")
