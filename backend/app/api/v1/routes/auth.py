from fastapi import Request, APIRouter, Depends, HTTPException, status, Body, Request, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging

from app import models, schemas, utils, database, config
from app.security import create_access_token

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


@router.post("/register", response_model=schemas.UserResponse, status_code=201)

def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):

    existing = db.query(models.User).filter(models.User.email == user.email).first()

    if existing:

        raise HTTPException(status_code=400, detail="Email já registrado")

    hashed_pw = utils.hash_password(user.password)

    new_user = models.User(

        email=user.email,

        full_name=user.full_name,

        password_hash=hashed_pw,

        type=getattr(user, "type", "pf"),

    )

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
