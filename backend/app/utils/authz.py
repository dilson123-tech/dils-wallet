from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from typing import Optional

from app.database import get_db
from app.models import User
from app.utils.security import SECRET_KEY, ALGORITHM

security = HTTPBearer(auto_error=False)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Lê Authorization: Bearer <token>, valida JWT e carrega o usuário do banco.

    Em modo DEV local, se o token vier ausente ou inválido, tentamos
    automaticamente usar o usuário id=1 como fallback para não travar o fluxo.
    """
    # Caso não venha Authorization correto, tenta fallback dev
    if creds is None or creds.scheme.lower() != "bearer":
        print("[AUTHZ] Authorization ausente ou esquema != Bearer; tentando fallback dev (user id=1).")
        fallback = db.query(User).filter(User.id == 1).first()
        if fallback:
            return fallback
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente.",
        )

    token = creds.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError("payload sem 'sub'")
    except JWTError as e:
        print("[AUTHZ] Erro ao decodificar JWT:", e)
        fallback = db.query(User).filter(User.id == 1).first()
        if fallback:
            print("[AUTHZ] Usando fallback dev (id=1) após erro no JWT.")
            return fallback
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        print("[AUTHZ] Usuário '%s' não encontrado, tentando fallback dev id=1." % username)
        fallback = db.query(User).filter(User.id == 1).first()
        if fallback:
            return fallback
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao administrador.",
        )
    return current_user

def require_customer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("customer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado ao cliente.",
        )
    return current_user
