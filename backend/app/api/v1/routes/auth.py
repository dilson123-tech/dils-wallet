from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app import database, models
from backend.app.auth import create_access_token_for_user
from backend.app.utils import verify_password  # se não existir, use: from backend.app.utils import verify_password


# Tenta achar o modelo User em caminhos comunstry:
router = APIRouter(prefix="/auth", tags=["auth"])


 class LoginRequest(BaseModel):
    username: Optional[str] = None
    email:    Optional[EmailStr] = None
    password: str

@router.post("/login", summary="Login")
def login(payload: LoginRequest, db: Session = Depends(database.get_db)):
    # aceita tanto username quanto email (no seu schema usamos email)
    login_id = payload.username or payload.email
    if not login_id:
        raise HTTPException(status_code=422, detail="username or email required")

    # seu modelo tem só email; então buscamos por email mesmo
    user = db.query(models.User).filter(models.User.email == login_id).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    access_token = create_access_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/ping", summary="Auth ping")
def ping():
    return {"ok": True}
