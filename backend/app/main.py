from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models
from .database import engine, Base, get_db

# �� Criação de tabelas
Base.metadata.create_all(bind=engine)

# 🚀 Inicializa o app
app = FastAPI(title="Aurea Gold Backend", version="1.0")

# 💚 Rota de healthcheck (para Railway)
@app.get("/health")
def health():
    return {"status": "ok", "service": "dils-wallet"}

# 🌐 CORS — libera apenas o front oficial
origins = [
    "https://aurea-gold-client-production.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root_index():
    return {"status": "ok", "service": "dils-wallet", "root": True}
