from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.idempotency import IdempotencyKey
from app.models.pix_transaction import PixTransaction

# tentamos importar o usuário principal; se não existir, tratamos
try:
    from app.models.user_main import User as UserMain
except Exception:  # pragma: no cover
    UserMain = None  # fallback p/ ambientes antigos

router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

# ---------------------------------------------------------------------------
# Regras de taxa (MODO LAB)
# ---------------------------------------------------------------------------
# Por enquanto, taxa fixa de 0,80% em envios de PIX.
# Recebimentos futuros podem ter regra diferente (hoje só usamos "envio").
FEE_PERCENTUAL_ENVIO = 0.80  # 0.80%


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
    Busca user id=1 se existir; retorna None se não existir
    ou se UserMain não estiver disponível.
    """
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
        # ------------------------------------------------------------------
        # Idempotência (header ganha do body)
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # Resolve usuário remetente
        # ------------------------------------------------------------------
        # 1) tenta por e-mail SE o modelo tiver .email
        user = _get_user_by_email(db, x_user_email)
        # 2) fallback: id=1
        if not user:
            user = _get_user_fallback_id1(db)

        if not user:
            return JSONResponse(
                {
                    "error": "sender_not_found",
                    "detail": (
                        "Modelo de usuário não tem coluna 'email' ou usuário id=1 "
                        "não existe. Crie um usuário id=1 ou ajuste a resolução."
                    ),
                    "hint_seed": "crie um usuário com id=1 no seu UserMain",
                },
                status_code=400,
            )

        # ------------------------------------------------------------------
        # Cálculo de taxa e valor líquido (MODO LAB)
        # ------------------------------------------------------------------
        valor_bruto = float(payload.valor)

        # somente envios pagam taxa por enquanto
        taxa_percentual = FEE_PERCENTUAL_ENVIO
        taxa_valor = round(valor_bruto * (taxa_percentual / 100.0), 2)
        valor_liquido = round(valor_bruto - taxa_valor, 2)
        if valor_liquido < 0:
            valor_liquido = 0.0

        descricao = (payload.msg or "").strip() or "PIX"

        # ------------------------------------------------------------------
        # Cria transação de envio com taxas preenchidas
        # ------------------------------------------------------------------
        tx = PixTransaction(
            user_id=user.id,
            tipo="envio",
            valor=valor_bruto,
            descricao=descricao,
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
                "taxa_percentual": float(tx.taxa_percentual or 0),
                "taxa_valor": float(tx.taxa_valor or 0),
                "valor_liquido": float(tx.valor_liquido or 0),
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
    u = None

    if UserMain and x_user_email:
        try:
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
                    break

    if u:
        q = q.filter(PixTransaction.user_id == u.id)

    txs = (
        q.order_by(PixTransaction.id.desc())
        .limit(min(max(limit, 1), 100))
        .all()
    )

    resp = []
    for t in txs:
        resp.append(
            {
                "id": t.id,
                "tipo": t.tipo,
                "valor": float(getattr(t, "valor", 0) or 0),
                "descricao": (getattr(t, "descricao", None) or "PIX"),
                "taxa_percentual": float(getattr(t, "taxa_percentual", 0) or 0),
                "taxa_valor": float(getattr(t, "taxa_valor", 0) or 0),
                "valor_liquido": float(
                    getattr(t, "valor_liquido", None)
                    or getattr(t, "valor", 0)
                    or 0
                ),
            }
        )

    return resp
