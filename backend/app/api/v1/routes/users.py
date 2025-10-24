from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import typing as t
import jwt

from app import database
from app.security import SECRET_KEY, ALGORITHM  # mesmos usados no login

# tenta achar o modelo User
try:
    from app.models.user import User
except Exception:
    from app.models.users import User  # fallback

router = APIRouter(tags=["users"])

@router.get("/me", summary="Who am I")
def me(authorization: t.Optional[str] = Header(None), db: Session = Depends(database.get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente.")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas ou token expirado.")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem 'sub'.")

    # buscar usuário por ID (login gera sub=str(uid))
    user = db.query(User).filter(getattr(User, "id") == int(sub)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    # montar resposta enxuta
    return {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "username": getattr(user, "username", None),
        "active": getattr(user, "is_active", True),
    }
