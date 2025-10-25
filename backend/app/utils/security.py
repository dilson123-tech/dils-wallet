from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
import secrets
import hashlib
import os

# ==========================
# CONFIG SENSÍVEL
# ==========================

SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-default-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = 30         # token curto
REFRESH_TOKEN_EXPIRE_DAYS = 7            # token longo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# --------------------------
# ACCESS TOKEN (JWT)
# --------------------------
def create_access_token(data: Dict[str, Any],
                        expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria JWT assinado (HS256) com expiração curta.
    data: ex {"sub": username}
    """
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return encoded_jwt

# --------------------------
# REFRESH TOKEN (opaco)
# --------------------------
def generate_refresh_token() -> str:
    """
    Gera um token aleatório grande, NÃO-JWT.
    Esse valor cru vai pro cliente.
    Só o hash fica no banco.
    """
    return secrets.token_urlsafe(48)

def hash_refresh_token(token: str) -> str:
    """
    Salva no banco só o hash SHA256 do refresh token.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def refresh_token_expiry_dt() -> datetime:
    """
    Retorna data/hora de expiração do refresh token.
    """
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
