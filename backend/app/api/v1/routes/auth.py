from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone

from app.database import get_db
from app.models.user_main import User
from app.models.refresh_token import RefreshToken
from app.utils.security import (
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry_dt,
)

# AUREA_DEBUG: logs sensíveis só com AUREA_DEBUG=1
import os
_AUREA_DEBUG = os.getenv('AUREA_DEBUG', '0') == '1'
def _dbg(*a, **k):
    if _AUREA_DEBUG:
        print(*a, **k)


router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    ident = (payload.username or "").strip()
    _dbg('[AUTH LOGIN] ident=', repr(ident), 'pwd_len=', len(payload.password))

    user = None

    # aceita email OU username
    if hasattr(User, "email") and ident:
        user = db.query(User).filter((User.email == ident) | (User.username == ident)).first()

    if not user and hasattr(User, "username") and ident:
        user = db.query(User).filter(User.username == ident).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    # hash no campo padrão do projeto
    pwd_hash = getattr(user, "hashed_password", None)
    _dbg('[AUTH LOGIN] user.id=', getattr(user,'id',None), 'username=', getattr(user,'username',None), 'email=', getattr(user,'email',None))

    if (not pwd_hash) or (not verify_password(payload.password, pwd_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    # sub do token: prioriza username, senão email
    sub = (getattr(user, "username", None) or getattr(user, "email", None) or ident)
    access_token = create_access_token({"sub": sub})

    raw_refresh = generate_refresh_token()
    hashed = hash_refresh_token(raw_refresh)

    token_row = RefreshToken(
        user_id=user.id,
        token_hash=hashed,
        expires_at=refresh_token_expiry_dt(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(token_row)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
    )


# ---------------------------
# Refresh token (JWT) - Aurea Gold
# ---------------------------
def _jwt_encode(payload: dict, secret: str, algo: str) -> str:
    try:
        from jose import jwt as _j
        return _j.encode(payload, secret, algorithm=algo)
    except Exception:
        import jwt as _j
        tok = _j.encode(payload, secret, algorithm=algo)
        return tok.decode("utf-8") if isinstance(tok, (bytes, bytearray)) else str(tok)

def _jwt_decode(token: str, secret: str, algo: str) -> dict:
    try:
        from jose import jwt as _j
        return _j.decode(token, secret, algorithms=[algo])
    except Exception:
        import jwt as _j
        return _j.decode(token, secret, algorithms=[algo])

def create_refresh_token(subject: str) -> str:
    import os
    from datetime import datetime, timedelta

    secret = globals().get("SECRET_KEY") or os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or "DEV_SECRET_CHANGE_ME"
    algo = globals().get("ALGORITHM") or os.getenv("JWT_ALGORITHM") or "HS256"
    days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    exp = datetime.utcnow() + timedelta(days=days)
    payload = {"sub": subject, "typ": "refresh", "exp": exp}
    return _jwt_encode(payload, secret, algo)

def decode_refresh_token(token: str) -> dict:
    import os
    secret = globals().get("SECRET_KEY") or os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or "DEV_SECRET_CHANGE_ME"
    algo = globals().get("ALGORITHM") or os.getenv("JWT_ALGORITHM") or "HS256"
    payload = _jwt_decode(token, secret, algo)
    if payload.get("typ") != "refresh":
        raise ValueError("token typ != refresh")
    if not payload.get("sub"):
        raise ValueError("missing sub")
    return payload

# endpoint: /api/v1/auth/refresh  (fica no mesmo router do auth.py)
try:
    from pydantic import BaseModel
    from fastapi import HTTPException
except Exception:
    BaseModel = object  # fallback (não deve acontecer)

class RefreshRequest(BaseModel):
    refresh_token: str

# se já existir TokenResponse/Token, a gente não briga: só adiciona o campo no retorno do login
@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    rt = (body.refresh_token or "").strip()
    if not rt:
        raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

    # Caso JWT (3 partes) — compat futuro
    if rt.count(".") == 2:
        try:
            payload = decode_refresh_token(rt)
            sub = payload.get("sub") if isinstance(payload, dict) else payload["sub"]
        except Exception:
            raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

        try:
            new_access = create_access_token({"sub": sub})
        except Exception:
            new_access = create_access_token(sub=sub)  # type: ignore

        new_refresh = create_refresh_token(sub)
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

    # Caso OPACO (sem pontos) — DB guarda token_hash (sha256 do token puro)
    from datetime import datetime, timezone, timedelta
    import secrets, hashlib

    try:
        from app.models.refresh_token import RefreshToken
    except Exception:
        raise HTTPException(status_code=500, detail="Modelo RefreshToken não encontrado")

    if not hasattr(RefreshToken, "token_hash"):
        raise HTTPException(status_code=500, detail="RefreshToken sem coluna token_hash")

    rt_hash = hashlib.sha256(rt.encode("utf-8")).hexdigest()

    obj = db.query(RefreshToken).filter(RefreshToken.token_hash == rt_hash).first()
    if not obj:
        # fallback ultra-legacy (se algum dia foi salvo “sem hash”)
        obj = db.query(RefreshToken).filter(RefreshToken.token_hash == rt).first()

    if not obj:
        raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

    now = datetime.now(timezone.utc)

    exp = getattr(obj, "expires_at", None)
    if exp:
        try:
            if getattr(exp, "tzinfo", None) is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if now >= exp:
                raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")
        except HTTPException:
            raise
        except Exception:
            pass

    # resolve sub via user_id -> User
    sub = None
    uid = getattr(obj, "user_id", None)
    if uid is not None:
        try:
            from app.models.user_main import User
            u = db.query(User).get(uid)
            if u:
                sub = getattr(u, "username", None) or getattr(u, "email", None)
        except Exception:
            sub = None

    if not sub:
        raise HTTPException(status_code=401, detail="Refresh token inválido/expirado")

    try:
        new_access = create_access_token({"sub": sub})
    except Exception:
        new_access = create_access_token(sub=sub)  # type: ignore

    # rotaciona: novo token puro -> salva hash
    new_rt = secrets.token_hex(32)
    obj.token_hash = hashlib.sha256(new_rt.encode("utf-8")).hexdigest()

    if hasattr(obj, "expires_at"):
        obj.expires_at = now + timedelta(days=30)

    db.add(obj)
    db.commit()

    return {"access_token": new_access, "refresh_token": new_rt, "token_type": "bearer"}

