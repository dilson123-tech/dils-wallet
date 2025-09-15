from fastapi import Request, APIRouter, Depends, HTTPException, status, Body, Request, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app import models, schemas, utils, database, config
from app.security import create_access_token

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse, status_code=201)

async def register(request: Request, db: Session = Depends(database.get_db)):

    try:

        payload = await request.json()

    except Exception:

        raise HTTPException(status_code=400, detail="JSON inválido")

    if not isinstance(payload, dict):

        raise HTTPException(status_code=422, detail="Corpo deve ser JSON object")

    email = payload.get("email")

    password = payload.get("password")

    full_name = payload.get("full_name")

    if not isinstance(email, str) or not isinstance(password, str):

        raise HTTPException(status_code=422, detail="Campos email e password são obrigatórios")

    existing = db.query(models.User).filter(models.User.email == email).first()

    if existing:

        raise HTTPException(status_code=400, detail="Email já registrado")

    hashed_pw = utils.hash_password(password)

    new_user = models.User(email=email, full_name=full_name, password_hash=hashed_pw)

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
