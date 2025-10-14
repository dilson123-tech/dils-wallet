import os, secrets, uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from fastapi import Request
from jose import jwt
from sqlalchemy.orm import Session

from backend.app.security.token_hash import refresh_hash
from backend.app.models.refresh_token import RefreshToken

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGO = os.getenv("JWT_ALGO", "HS256")
ACCESS_MIN = int(os.getenv("JWT_ACCESS_EXPIRE_MIN", "15"))
REFRESH_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))
REFRESH_ROTATE = os.getenv("JWT_REFRESH_ROTATE", "true").lower() == "true"

def create_access_token(sub: str, extra: Optional[Dict]=None, minutes: Optional[int]=None) -> str:
    now = datetime.utcnow()
    exp = now + timedelta(minutes=minutes or ACCESS_MIN)
    payload = {"sub": sub, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    if extra: payload.update(extra)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGO)

def decode_access_token(token: str) -> Dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGO])

def _client_meta(req: Request):
    ip = req.headers.get("x-forwarded-for", "").split(",")[0].strip() or (req.client.host if req.client else None)
    ua = req.headers.get("user-agent")
    return ip, ua

def issue_refresh_token(db: Session, user_id: str, req: Request) -> Tuple[str, RefreshToken]:
    raw = secrets.token_urlsafe(48)
    h = refresh_hash(raw)
    jti = uuid.uuid4().hex
    ip, ua = _client_meta(req)
    rt = RefreshToken(
        user_id=user_id, jti=jti, token_hash=h,
        ip=ip, user_agent=ua,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_DAYS),
        active=True,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return raw, rt

def revoke_refresh(db: Session, jti: str):
    rt = db.query(RefreshToken).filter(RefreshToken.jti == jti, RefreshToken.active == True).first()
    if rt:
        rt.active = False
        rt.revoked_at = datetime.utcnow()
        db.commit()
    return rt

def verify_and_rotate_refresh(db: Session, raw_token: str, req: Request) -> Tuple[str, str]:
    if not raw_token:
        raise ValueError("missing refresh token")
    h = refresh_hash(raw_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == h, RefreshToken.active == True).first()
    if not rt:
        raise ValueError("not found or revoked")
    if rt.expires_at <= datetime.utcnow():
        rt.active = False; db.commit()
        raise ValueError("expired")
    access = create_access_token(str(rt.user_id))
    new_raw = ""
    if REFRESH_ROTATE:
        rt.active = False
        rt.revoked_at = datetime.utcnow()
        db.commit()
        new_raw, _ = issue_refresh_token(db, str(rt.user_id), req)
    return access, new_raw
