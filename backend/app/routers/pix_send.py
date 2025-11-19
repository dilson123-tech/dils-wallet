from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models.idempotency import IdempotencyKey

# tentamos importar o usuário principal; se não existir, tratamos
try:
    from app.models.user_main import User as UserMain
except Exception:  # pragma: no cover
    UserMain = None  # fallback p/ ambientes antigos

router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

class PixSendPayload(BaseModel):
    dest: str = Field(..., description="Email/Chave destino")
    valor: float = Field(..., gt=0, description="Valor em reais")
    msg: Optional[str] = Field(default="", description="Descrição/memo da transação")
    idem_key: Optional[str] = Field(default=None, description="Idempotency-Key opcional")

def _get_user_by_email(db: Session, email: Optional[str]):
    """Tenta buscar por e-mail apenas se o modelo tiver o atributo .email"""
    if not email or UserMain is None:
        return None
    email_attr = getattr(UserMain, "email", None)
    if email_attr is None:
        # modelo não tem coluna email
        return None
    return db.query(UserMain).filter(email_attr == email).first()

def _get_user_fallback_id1(db: Session):
    """Busca user id=1 se existir; retorna None se não existir ou se UserMain não estiver disponível."""
    if UserMain is None:
        return None
    try:
        return db.get(UserMain, 1)  # SQLAlchemy 2.x-style
    except Exception:
        # compat c/ SQLAlchemy 1.x
        try:
            return db.query(UserMain).get(1)
        except Exception:
            return None

@router.post("/send", summary="Pix Send")
def pix_send(
    payload: PixSendPayload,
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
    x_idem_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    try:
        # idempotência (header ganha do body)
        idem_key = x_idem_key or payload.idem_key
        if idem_key:
            existing = db.query(IdempotencyKey).filter(IdempotencyKey.key == idem_key).first()
            if existing:
                return JSONResponse({"status": "duplicate", "idem_key": idem_key}, status_code=200)

        # Resolve usuário:
        # 1) tenta por e-mail SE o modelo tiver .email
        user = _get_user_by_email(db, x_user_email)
        # 2) fallback: id=1
        if not user:
            user = _get_user_fallback_id1(db)

        if not user:
            return JSONResponse(
                {
                    "error": "sender_not_found",
                    "detail": "Modelo de usuário não tem coluna 'email' ou usuário id=1 não existe. Crie um usuário id=1 ou ajuste a resolução.",
                    "hint_seed": "crie um usuário com id=1 no seu UserMain",
                },
                status_code=400,
            )

        # cria transação (garante descricao != NULL)
        tx = PixTransaction(
            user_id=user.id,
            tipo="envio",
            valor=float(payload.valor),
            descricao=(payload.msg or "").strip(),
        )
        db.add(tx)

        if idem_key:
            db.add(IdempotencyKey(key=idem_key))

        db.commit()
        db.refresh(tx)

        return {
            "ok": True,
            "tx": {
                "id": tx.id,
                "user_id": tx.user_id,
                "tipo": tx.tipo,
                "valor": tx.valor,
                "descricao": tx.descricao,
            },
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        return JSONResponse(
            {"error": "sql_error", "detail": str(e.__cause__ or e)}, status_code=500
        )
    except Exception as e:
        return JSONResponse(
            {"error": "internal_error", "detail": str(e)}, status_code=500
        )

# --- list endpoint (fix) ---
@router.get("/list")
def pix_list(
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    limit: int = 50,
):
    q = db.query(PixTransaction)
    if UserMain and x_user_email:
        u = None
    if UserMain:
        try:
            col = getattr(UserMain, "email")
            u = db.query(UserMain).filter(col == x_user_email).first()
        except AttributeError:
            # tenta campos comuns caso "email" não exista
            for attr in ("user_email","mail","username","login"):
                if hasattr(UserMain, attr):
                    u = db.query(UserMain).filter(getattr(UserMain, attr) == x_user_email).first()
                    break
        if u:
            q = q.filter(PixTransaction.user_id == u.id)
    txs = q.order_by(PixTransaction.id.desc()).limit(min(max(limit,1),100)).all()
    return [
        {"id": t.id, "tipo": t.tipo, "valor": float(t.valor or 0), "descricao": t.descricao or "PIX"}
        for t in txs
    ]
