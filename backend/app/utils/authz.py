from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from jose import jwt
from jose.exceptions import JWTError
import os

from app.database import get_db
from app.models.user_main import User
from app.utils.security import SECRET_KEY, ALGORITHM


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado.",
    )

    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise credentials_exception

    token = auth.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(
        or_(User.username == username, User.email == username)
    ).first()

    if user is None:
        raise credentials_exception

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if getattr(current_user, "is_admin", False):
        return current_user
    raise HTTPException(status_code=403, detail="Acesso negado.")


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    return current_user
