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
