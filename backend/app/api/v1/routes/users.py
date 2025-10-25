from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import typing as t
import jwt

from app import database
from app.security import get_secret_key, get_algorithm

# tenta achar o modelo User
try:
    from app.models.user import User
except Exception:
    from app.models.users import User  # fallback para nome alternativo

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/me", summary="Who am I")
def me(
    authorization: t.Optional[str] = Header(None),
    db: Session = Depends(database.get_db),
):
    # header ausente ou malformado
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente.",
        )

    token = authorization.split(" ", 1)[1]

    # valida token
    try:
        payload = jwt.decode(
            token,
            get_secret_key(),
            algorithms=[get_algorithm()],
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou token expirado.",
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem 'sub'.",
        )

    # buscar usuário no banco usando o sub como id
    user = db.query(User).filter(getattr(User, "id") == int(sub)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    # resposta pública / limpa
    return {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "username": getattr(user, "username", None),
        "active": getattr(user, "is_active", True),
    }
