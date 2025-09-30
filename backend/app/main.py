import os
import importlib
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# DB
from .database import engine, Base, get_db  # mantém como está no projeto

# App
app = FastAPI(title="Dils Wallet API", version="0.1.0")

# CORS
CORS_ORIGINS: List[str] = []
env_origins = os.getenv("CORS_ORIGINS", "")
if env_origins:
    CORS_ORIGINS = [o.strip() for o in env_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static UI (só monta se a pasta existir)
UI_DIR = os.getenv("UI_DIR", str(Path(__file__).resolve().parent.parent / "ui"))
if Path(UI_DIR).is_dir():
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")

# Health
@app.get("/api/v1/health")
def health() -> Response:
    return Response(status_code=200)

# Teste de DB (204 se conectar)
@app.get("/api/v1/users/test-db")
def test_db(_: Session = Depends(get_db)) -> Response:
    return Response(status_code=204)

# Startup: cria tabelas (seguro)
@app.on_event("startup")
def on_startup() -> None:
    import os
    print('[startup] PORT=', os.getenv('PORT'))
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # não derruba o boot por erro de migração
        # Log simples via print; Railway captura stdout
        print(f"[startup] warning: create_all failed: {exc!r}")

# Routers (import tardio para evitar ciclos)
def _include_routes() -> None:
    auth_mod = importlib.import_module("backend.app.api.v1.routes.auth")
    users_mod = importlib.import_module("backend.app.api.v1.routes.users")
    tx_mod = importlib.import_module("backend.app.api.v1.routes.transactions")

    app.include_router(auth_mod.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users_mod.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(tx_mod.router, prefix="/api/v1/transactions", tags=["transactions"])

_include_routes()
