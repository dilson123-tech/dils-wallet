from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone

from app.database import get_db
from app.models import User, RefreshToken
from app.utils.security import (
    create_access_token,
    hash_refresh_token,
)

router = APIRouter()

class RefreshRequest(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    """
    Recebe um refresh_token cru, valida e devolve novo access_token curto.
    """
    hashed = hash_refresh_token(body.refresh_token)

    token_row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hashed)
        .first()
    )

    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )

    # expirou?
    if token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado"
        )

    # pega o usuário dono
    user = db.query(User).filter(User.id == token_row.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )

    new_access = create_access_token({"sub": user.username})

    return AccessTokenResponse(
        access_token=new_access,
        token_type="bearer"
    )
