from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Numeric
from sqlalchemy.exc import IntegrityError
import hashlib, json

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models.pix_ledger import PixLedger

# Modelo de usuário pode variar
try:
    from app.models.user_main import User as UserMain
except Exception:
    UserMain = None

# Idempotência (tabela precisa ter UNIQUE(key))
try:
    from app.models.idempotency import IdempotencyKey
except Exception:
    IdempotencyKey = None

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
    Usa o primeiro usuário existente; se tabela estiver vazia, cria um seed mínimo.
    """
    if not UserMain:
        raise HTTPException(status_code=400, detail="user_table_missing: tabela de usuários indisponível")

    u = db.query(UserMain).first()
    if u:
        return int(getattr(u, "id"))

    # seed mínimo
    cols = {c.name for c in UserMain.__table__.columns}
    alias_email = email_hint or "seed@aurea.local"
    alias_name = (alias_email.split("@")[0] if "@" in alias_email else alias_email)
    data = {}
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
        u = UserMain(**data)
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
    idem_key: str | None = Header(None, alias="X-Idempotency-Key", convert_underscores=False),
):
    desc = (payload.msg or payload.descricao or "").strip() or "PIX"
    try:
        user_email = _get_user_email(request, x_user_email)
        uid = _ensure_user_id(db, user_email)

        # --- Idempotência (opcional, se tabela existir) ---
        if IdempotencyKey and idem_key:
            fp_data = {
                "k": idem_key,
                "u": uid,
                "path": "/api/v1/pix/send",
                "payload": {"dest": payload.dest, "valor": float(payload.valor), "msg": desc},
            }
            fp = hashlib.sha256(json.dumps(fp_data, sort_keys=True).encode()).hexdigest()
            try:
                rec = IdempotencyKey(key=fp)  # coluna 'key' deve ser UNIQUE
                db.add(rec)
                db.commit()
                db.refresh(rec)
            except IntegrityError:
                db.rollback()
                return JSONResponse({"ok": True, "idem": True, "detail": "duplicate_suppressed"})

        tx = PixTransaction(
            user_id=uid,
            tipo="envio",
            valor=float(payload.valor),
            descricao=desc
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        try:
            led = PixLedger(user_id=uid, kind="debit", amount=float(payload.valor), ref_tx_id=tx.id, description=desc or "PIX")
            db.add(led)
            db.commit()
        except Exception:
            db.rollback()
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

@router.get("/pix/saldo")
def pix_saldo(
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email", convert_underscores=False),
):
    """
    Saldo contábil por usuário a partir do ledger (credit - debit).
    """
    try:
        user_email = _get_user_email(request, x_user_email)
        uid = _ensure_user_id(db, user_email)
        from app.models.pix_ledger import PixLedger
        saldo = db.query(
            func.coalesce(
                func.sum(
                    case(
                        (PixLedger.kind == "credit", cast(PixLedger.amount, Numeric(14,2))),
                        else_=-cast(PixLedger.amount, Numeric(14,2))
                    )
                ), 0
            )
        ).filter(PixLedger.user_id == uid).scalar() or 0
        return {"ok": True, "saldo": float(saldo)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pix_saldo_failed: {e}")

@router.get("/pix/balance")
def pix_balance_alias(
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email", convert_underscores=False),
):
    return pix_saldo(request, db, x_user_email)
