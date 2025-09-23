import os, time
from datetime import timedelta
from typing import Optional, Dict
import jwt  # PyJWT

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-override-me")
ALGORITHM  = "HS256"

def _exp_ts(delta: timedelta) -> int:
    return int(time.time() + delta.total_seconds())

def create_access_token(data: Dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = _exp_ts(expires_delta)
    payload["typ"] = "access"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_refresh_token(token: str) -> Optional[Dict]:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if data.get("typ") != "refresh":
            return None
        return data
    except Exception:
        return None


def create_refresh_token(data: Dict, expires_delta: timedelta = timedelta(days=7)) -> str:
    payload = data.copy()
    payload["exp"] = _exp_ts(expires_delta)
    payload["typ"] = "refresh"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
