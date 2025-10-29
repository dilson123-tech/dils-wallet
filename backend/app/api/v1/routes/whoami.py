from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
import jwt
import time

from app.database import get_db
from app.models import User  # User vem de app/models/__init__.py
from app.auth import JWT_SECRET, JWT_ALG  # segredo e algoritmo do token

router = APIRouter(tags=["auth"])

def get_user_from_claims(claims: dict, db: Session) -> Optional[User]:
    ident = claims.get("sub") or claims.get("username") or claims.get("email")

    if not ident:
        return None

    # tenta identificar por id ou email
    try:
        # se ident é número -> tenta id
        if isinstance(ident, str) and ident.isdigit():
            return db.query(User).filter(User.id == int(ident)).first()
        # senão tenta por email
        return db.query(User).filter(User.email == ident).first()
    except Exception:
        return None

@router.get("/api/v1/whoami")
def whoami(
    authorization: Optional[str] = Header(None)
    # ex: "Authorization: Bearer <token>"
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="missing_bearer_token"
        )

    token = authorization.split(" ", 1)[1].strip()

    # valida token JWT
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token_expired")
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_token")

    # checa exp
    exp = claims.get("exp")
    if exp and time.time() > float(exp):
        raise HTTPException(status_code=401, detail="token_expired")

    # abre sessão no banco e resolve usuário
    db = next(get_db())
    user = get_user_from_claims(claims, db)

    if not user:
        raise HTTPException(status_code=401, detail="user_not_found_for_token")

    # checa status do usuário (ativos, verificados, etc.)
    if hasattr(user, "is_active") and not getattr(user, "is_active"):
        raise HTTPException(status_code=401, detail="user_inactive")
    if hasattr(user, "is_verified") and not getattr(user, "is_verified"):
        raise HTTPException(status_code=401, detail="user_unverified")

    return {
        "ok": True,
        "user": {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "full_name": getattr(user, "full_name", None),
            "type": getattr(user, "type", None),
            "role": getattr(user, "role", None),
        },
        "claims": {k: v for k, v in claims.items() if k not in ("exp", "iat")},
        "algo": JWT_ALG,
    }
