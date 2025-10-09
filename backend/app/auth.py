from backend.app import config
import os
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models, schemas, utils, config, database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Criar token JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)
    return encoded_jwt

# Obter usuário pelo token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
# --- JWT fallbacks (env/config) ---
import os
JWT_ALG = getattr(config, "ALGORITHM", getattr(config, "JWT_ALGORITHM", "HS256"))
JWT_SECRET = getattr(config, "SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret"))
JWT_EXPIRE_MINUTES = int(getattr(
    config, "ACCESS_TOKEN_EXPIRE_MINUTES",
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
))
