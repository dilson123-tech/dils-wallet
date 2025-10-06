from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app import database as database
from backend.app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginIn(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(body: LoginIn, db: Session = Depends(database.get_db)):
    # tenta diferentes nomes de coluna conforme seu schema
    q = text("""
        SELECT id, username,
               COALESCE(password_hash, hashed_password, password) AS pwd
        FROM users
        WHERE username = :u
        LIMIT 1
    """)
    row = db.execute(q, {"u": body.username}).mappings().first()
    if not row or not verify_password(body.password, row["pwd"] or ""):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = create_access_token(sub=str(row["id"]), extra={"username": row["username"]})
    return {"access_token": token, "token_type": "bearer"}
