from app.security import create_access_token
from app.security import create_access_token
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app import models, schemas, utils, database, config

router = APIRouter()

# Registrar usuário
from fastapi import Body
@router.post("/register", response_model=schemas.UserResponse)
def register(payload: schemas.UserCreate = Body(...), db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == payload.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    hashed_pw = utils.hash_password(payload.password)
    new_user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        
        password_hash=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Login
@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}
