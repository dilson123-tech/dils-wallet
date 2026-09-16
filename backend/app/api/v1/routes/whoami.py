from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional
import jwt

from app.models import User  # User vem de app/models/__init__.py
from app.utils.authz import require_customer
from app.utils.security import SECRET_KEY, ALGORITHM

router = APIRouter(tags=["auth"])


@router.get("/api/v1/whoami")
def whoami(
    authorization: Optional[str] = Header(None),
    current_user: User = Depends(require_customer),
):
    """Identidade e claims do usuário autenticado.

    A resolução do usuário vem sempre de Depends(require_customer) --
    o mesmo pipeline canônico usado em /api/v1/users/me
    (app/utils/authz.py::get_current_user). Nunca mais interpreta um
    claim "sub" numérico como User.id cru: se o token não passar pela
    validação canônica (assinatura, expiração, sub == username/email
    de um usuário real), a própria dependência já responde 401 antes
    deste corpo rodar.

    O token só é decodificado de novo aqui para ecoar "claims"/"algo"
    no contrato de resposta já existente -- isso nunca influencia
    quem é o usuário retornado.
    """
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        claims = {}

    if hasattr(current_user, "is_active") and not getattr(current_user, "is_active"):
        raise HTTPException(status_code=401, detail="user_inactive")
    if hasattr(current_user, "is_verified") and not getattr(current_user, "is_verified"):
        raise HTTPException(status_code=401, detail="user_unverified")

    return {
        "ok": True,
        "user": {
            "id": getattr(current_user, "id", None),
            "email": getattr(current_user, "email", None),
            "full_name": getattr(current_user, "full_name", None),
            "type": getattr(current_user, "type", None),
            "role": getattr(current_user, "role", None),
        },
        "claims": {k: v for k, v in claims.items() if k not in ("exp", "iat")},
        "algo": ALGORITHM,
    }
