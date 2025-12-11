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
    user = (
        db.query(User)
        .filter(User.username == payload.username)
        .first()
    )

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    # gera access_token (JWT curto)
    access_token = create_access_token({"sub": user.username})

    # gera refresh token opaco e guarda o hash no banco
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
        refresh_token=raw_refresh,  # mandamos o valor cru pro cliente
        token_type="bearer",
    )
