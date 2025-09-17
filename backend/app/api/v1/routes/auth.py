from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging
import traceback, traceback

from app import models, schemas, utils, database, config
from app.security import create_access_token

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # já existe?
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email já registrado")

    # criar
    hashed = utils.hash_password(user.password)
    new_user = models.User(
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed,
    )

    # coluna type (se NOT NULL no schema)
    if hasattr(models.User, "type"):
        col = getattr(models.User.__table__.c, "type", None)  # type: ignore[attr-defined]
        if col is not None and not getattr(col, "nullable", True) and getattr(new_user, "type", None) in (None, ""):
            setattr(new_user, "type", "pf")

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}

# endpoint canário pra confirmar arquivo carregado em prod
@router.get("/_version")
def _version():
    import os
    return {"marker": "AUTH_OK", "file": __file__}


@router.get("/db-ping")
def db_ping(db: Session = Depends(database.get_db)):
    # testa conexão e existência da tabela users
    try:
        db.execute(text("SELECT 1"))
        ok = True
    except Exception as e:
        logger.error("db-ping failed: %s", e)
        ok = False
    # tenta contar users (pode falhar se tabela não existir)
    count = None
    try:
        count = db.query(models.User).count()
    except Exception as e:
        logger.error("users count failed: %s", e)
    return {"db_ok": ok, "users_count": count}

@router.post("/register_echo")
def register_echo(payload: dict):
    return {"echo": payload}

@router.post("/register2", status_code=201)
def register2(payload: dict, db: Session = Depends(database.get_db)):
    try:
        email = payload.get("email"); pwd = payload.get("password"); full = payload.get("full_name")
        if not email or not pwd:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="email e password são obrigatórios")
        if db.query(models.User).filter(models.User.email == email).first():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Email já registrado")
        hashed = utils.hash_password(pwd)
        u = models.User(email=email, full_name=full, password_hash=hashed)
        if hasattr(models.User, "type"):
            col = getattr(models.User.__table__.c, "type", None)
            if col is not None and not getattr(col, "nullable", True) and getattr(u, "type", None) in (None, ""):
                setattr(u, "type", "pf")
        db.add(u); db.commit(); db.refresh(u)
        return {"id": u.id, "email": u.email, "full_name": u.full_name}
    except Exception as e:
        logger.error("register2 failed: %s", e); logger.error(traceback.format_exc())
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"register2 failed: {e.__class__.__name__}: {e}")
