from fastapi import Response, FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import time

from . import models
from .database import engine, Base, get_db

# garante tabelas no banco
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Dils Wallet API",
    version="0.1.0",
)

# se existir pasta "ui", serve ela
app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

# CORS aberto (ajustar depois)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# endpoint que o Railway usa pra healthcheck
@app.get("/healthz")
def healthz():
    return {"status": "ok", "ts": int(time.time())}

# só pra validar DB rapidamente
@app.get("/users/test-db")
def test_db(db: Session = Depends(get_db)):
    return {"msg": "DB conectado!"}

# importante: NÃO importa routers de auth/users/etc aqui.
# versão mínima só pra subir saudável em produção.
