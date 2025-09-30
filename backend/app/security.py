from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app import models, database, config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(database.get_db)) -> Any:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido (sem sub)")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user = db.query(UserORM).filter(UserORM.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return user
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm="HS256")

from typing import Any, TYPE_CHECKING
try:
    from app import models  # pacote principal (pode não ter User)
except Exception:
    models = None

# tenta importar User do pacote models; se falhar, cai para models_base
try:
from .models import User as UserORM  # type: ignore
except Exception:
    try:
from .models_base import User as UserORM  # type: ignore
    except Exception:
        UserORM = None  # fallback duro: sem modelo de usuário
