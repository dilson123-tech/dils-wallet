from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from jose import jwt, JWTError
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.auth import JWT_SECRET, JWT_ALG  # <- usa o MESMO segredo/algoritmo do emissor
import re, time

router = APIRouter(tags=["Auth"])

def _get_user_from_claims(claims):
    db = SessionLocal()
    try:
        ident = claims.get("sub") or claims.get("username") or claims.get("email")
        if not ident:
            return None
        if isinstance(ident, str) and re.fullmatch(r"\d+", ident):
            return db.query(User).filter(User.id == int(ident)).first()
        if isinstance(ident, str) and "@" in ident:
            return db.query(User).filter(User.email == ident).first()
        try:
            return db.query(User).filter(User.id == int(str(ident))).first()
        except:
            return None
    finally:
        db.close()

@router.get("/auth/whoami")
def whoami(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_bearer_token")
    token = authorization.split(" ", 1)[1].strip()

    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")

    exp = claims.get("exp")
    if exp and time.time() > float(exp):
        raise HTTPException(status_code=401, detail="token_expired")

    user = _get_user_from_claims(claims)
    if not user:
        raise HTTPException(status_code=401, detail="user_not_found_for_token")

    if hasattr(user, "is_active") and not getattr(user, "is_active"):
        raise HTTPException(status_code=401, detail="user_inactive")
    if hasattr(user, "is_verified") and not getattr(user, "is_verified"):
        raise HTTPException(status_code=401, detail="user_unverified")

    return {
        "ok": True,
        "user": {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "full_name": getattr(user, "full_name", None),
            "type": getattr(user, "type", None),
        },
        "claims": {k: v for k, v in claims.items() if k not in {"exp", "iat"}},
        "algo": JWT_ALG,
    }
