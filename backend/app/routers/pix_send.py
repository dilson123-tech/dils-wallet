from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

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
    """Tenta buscar por e-mail apenas se o modelo tiver o atributo .email."""
    if not email or UserMain is None:
        return None

    email_attr = getattr(UserMain, "email", None)
    if email_attr is None:
        # modelo não tem coluna email
        return None

    return db.query(UserMain).filter(email_attr == email).first()


def _get_user_fallback_id1(db: Session):
    """
    Busca user id=1 se existir; retorna None se não existir ou se UserMain não estiver disponível.
    """
    if UserMain is None:
        return None

    try:
        # SQLAlchemy 2.x-style
        return db.get(UserMain, 1)
    except Exception:
        # compat SQLAlchemy 1.x
        try:
            return db.query(UserMain).get(1)  # type: ignore[arg-type]
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
        # ---------------------------------------------------
        # Idempotência (header ganha do body)
        # ---------------------------------------------------
        idem_key = x_idem_key or payload.idem_key
        if idem_key:
            existing = (
                db.query(IdempotencyKey)
                .filter(IdempotencyKey.key == idem_key)
                .first()
            )
            if existing:
                return JSONResponse(
                    {"status": "duplicate", "idem_key": idem_key},
                    status_code=200,
                )

        # ---------------------------------------------------
        # Resolve usuário:
        # 1) tenta por e-mail SE o modelo tiver .email
        # 2) fallback: usuário id=1
        # 3) se ainda não achar, força user_id=1 (modo LAB local)
        # ---------------------------------------------------
        user = _get_user_by_email(db, x_user_email)

        if not user:
            user = _get_user_fallback_id1(db)

        if user:
            user_id = getattr(user, "id", 1)
        else:
            # modo LAB: ainda não temos user real, mas não vamos travar o fluxo
            user_id = 1

        # ---------------------------------------------------
        # Cria transação PIX com taxa da Aurea Gold.
        # Regra LAB:
        #   - taxa_percentual: 0.8 (%)
        #   - taxa_valor: valor * 0.8 / 100
        #   - valor_liquido: valor - taxa_valor
        # ---------------------------------------------------
        valor_bruto = float(payload.valor)
        taxa_percentual = 0.8  # 0.8% por envio
        taxa_valor = round(valor_bruto * (taxa_percentual / 100.0), 2)
        valor_liquido = valor_bruto - taxa_valor

        tx = PixTransaction(
            user_id=user_id,
            tipo="envio",
            valor=valor_bruto,
            descricao=(payload.msg or "").strip() or "PIX",
            taxa_percentual=taxa_percentual,
            taxa_valor=taxa_valor,
            valor_liquido=valor_liquido,
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
                "valor": float(tx.valor or 0),
                "descricao": tx.descricao or "PIX",
            },
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        return JSONResponse(
            {"error": "sql_error", "detail": str(e.__cause__ or e)},
            status_code=500,
        )
    except Exception as e:
        return JSONResponse(
            {"error": "internal_error", "detail": str(e)},
            status_code=500,
        )


# --- list endpoint (ajustado) ---
@router.get("/list")
def pix_list(
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
    limit: int = 50,
):
    q = db.query(PixTransaction)

    if UserMain and x_user_email:
        u = None
        try:
            # tenta campo email direto
            col = getattr(UserMain, "email")
            u = db.query(UserMain).filter(col == x_user_email).first()
        except AttributeError:
            # tenta campos comuns caso "email" não exista
            for attr in ("user_email", "mail", "username", "login"):
                if hasattr(UserMain, attr):
                    u = (
                        db.query(UserMain)
                        .filter(getattr(UserMain, attr) == x_user_email)
                        .first()
                    )
                    if u:
                        break

        if u:
            q = q.filter(PixTransaction.user_id == u.id)

    txs = (
        q.order_by(PixTransaction.id.desc())
        .limit(min(max(limit, 1), 100))
        .all()
    )

    return [
        {
            "id": t.id,
            "tipo": t.tipo,
            "valor": float(getattr(t, "valor", 0) or 0),
            "descricao": getattr(t, "descricao", None) or "PIX",
            "taxa_percentual": float(getattr(t, "taxa_percentual", 0) or 0),
            "taxa_valor": float(getattr(t, "taxa_valor", 0) or 0),
            "valor_liquido": float(
                getattr(t, "valor_liquido", getattr(t, "valor", 0)) or 0
            ),
        }
        for t in txs
    ]
