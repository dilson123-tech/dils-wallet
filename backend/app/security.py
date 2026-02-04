import os, time, typing as t
from datetime import timedelta
from jose import jwt
from passlib.hash import bcrypt

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-aura")  # defina em prod
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MIN", "60"))

def create_access_token(sub: str, extra: t.Optional[dict]=None) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + ACCESS_TOKEN_EXPIRE_MINUTES*60}
    if extra: payload.update(extra)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain: str, hashed: str) -> bool:
    # aceita tanto hash bcrypt quanto senha em texto (para migração)
    try:
        if hashed.startswith("$2b$") or hashed.startswith("$2a$"):
            return bcrypt.verify(plain, hashed)
    except Exception:
        pass
    return plain == hashed  # fallback migração

def hash_password(plain: str) -> str:
    return bcrypt.hash(plain)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app import models
import os

# Secret e algoritmo
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-aura")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decodifica o JWT e retorna o usuário autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(or_(models.User.username == username, models.User.email == username)).first()
    if user is None:
        raise credentials_exception

    return user
