from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app import database, models
from backend.app.oauth2 import create_access_token
from backend.app.utils import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

@router.post("/login", summary="Login")
def login(payload: LoginRequest, db: Session = Depends(database.get_db)):
    # aceita ambos, mas usa email do banco
    login_id = payload.username or payload.email
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="username or email required",
        )

    # seu modelo só tem 'email', então procuramos por email
    user = db.query(models.User).filter(models.User.email == login_id).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
        )

    access_token = create_access_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/ping", summary="Auth ping")
def ping():
    return {"ok": True}
# --- compat: manter a call-site que usa create_access_token_for_user(user)
def create_access_token_for_user(user):
    username_claim = getattr(user, "username", None) or getattr(user, "email", None) or ""
    return create_access_token({"sub": str(getattr(user, "id", "")), "username": username_claim})
