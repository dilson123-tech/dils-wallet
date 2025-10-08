from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app import database
from backend.app.security import create_access_token, verify_password

# Tenta achar o modelo User em caminhos comuns
try:
    from backend.app.models.user import User
except Exception:
    from backend.app.models.users import User  # fallback

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    username: str
    password: str

@router.post("/login", summary="Login")
def login(body: LoginIn, db: Session = Depends(database.get_db)):
    """
    Aceita JSON: {"username": "<email-ou-username>", "password": "..."}.
    Busca por email primeiro; se não existir campo 'email', tenta 'username'.
    Verifica hash usando verify_password do módulo security.
    """
    # Descobrir como consultar o usuário (email ou username)
    user = None
    if hasattr(User, "email"):
        user = db.query(User).filter(User.email == body.username).first()
    if user is None and hasattr(User, "username"):
        user = db.query(User).filter(User.username == body.username).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    # Descobrir campo do hash no modelo
    pwd_hash = None
    for cand in ("hashed_password", "password_hash", "password"):
        if hasattr(user, cand):
            pwd_hash = getattr(user, cand)
            break
    if not pwd_hash:
        raise HTTPException(status_code=500, detail="Configuração de senha ausente no modelo de usuário.")

    # Verificar senha
    if not verify_password(body.password, pwd_hash or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    # Descobrir id do usuário e um identificador para por no token
    uid = getattr(user, "id", None)
    if uid is None:
        raise HTTPException(status_code=500, detail="Usuário sem id.")

    username_claim = (
        getattr(user, "username", None)
        or getattr(user, "email", None)
        or body.username
    )

    token = create_access_token(sub=str(uid), extra={"username": username_claim})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/ping", summary="Auth ping")
def ping():
    return {"ok": True}
