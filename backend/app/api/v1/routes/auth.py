from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging

from app import models, schemas, utils, database, config
from app.security import create_access_token

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

@router.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register(req: Request, db: Session = Depends(database.get_db)):
    body = await req.json()
    logger.info("DEBUG register raw body: %s", body)

    try:
        user = schemas.UserCreate(**body)
    except Exception as e:
        logger.exception("Falha ao parsear UserCreate")
        raise HTTPException(status_code=400, detail=f"Erro parse: {e}")

    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email já registrado")

    hashed_pw = utils.hash_password(user.password)
    new_user = models.User(
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_pw,
    )

    if hasattr(models.User, "type"):
        col = getattr(models.User.__table__.c, "type", None)
        if col is not None and not getattr(col, "nullable", True) and getattr(new_user, "type", None) in (None, ""):
            setattr(new_user, "type", "pf")

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}
