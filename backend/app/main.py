from fastapi import FastAPI, Depends, Response
from sqlalchemy.orm import Session
import time

from . import models
from .database import engine, Base, get_db

# cria tabelas automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aurea Gold Backend", version="1.0.0")

@app.get("/healthz")
def healthz():
    """Usado pelo Railway para o Healthcheck"""
    return {"status": "ok", "service": "dils-wallet", "ts": int(time.time())}

@app.get("/")
def root():
    return {"status": "ok", "root": True}

@app.get("/users/test-db")
def test_db(db: Session = Depends(get_db)):
    return {"msg": "DB conectado!"}
