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
        user = db.query(User).filter(User.email == ident).first()

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
