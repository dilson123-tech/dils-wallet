from datetime import datetime, timedelta, timezone
import jwt  # PyJWT
from app import config  # usa SECRET_KEY já definida

ALGO = "HS256"

def _expire_in(minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)

def create_refresh_token(data: dict, expires_minutes: int = 60 * 24 * 7) -> str:
    """Gera um refresh token com expiração padrão de 7 dias."""
    to_encode = data.copy()
    to_encode.update({"exp": _expire_in(expires_minutes)})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGO)

def verify_refresh_token(token: str) -> dict:
    """
    Decodifica e retorna o payload.
    Pode levantar jwt.ExpiredSignatureError / jwt.InvalidTokenError.
    """
    return jwt.decode(token, config.SECRET_KEY, algorithms=[ALGO])
