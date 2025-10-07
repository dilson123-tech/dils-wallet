from backend.app.api.v1 import router as api_v1_router
import os
import importlib
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends
from backend.app.api.v1.register_auth import include_auth_routes
from backend.app.api.v1.register_daily import include_daily_routes
from backend.app.api.v1.register_daily import include_daily_routes
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# DB
from .database import engine, Base, get_db  # mantém como está no projeto

# App
app = FastAPI(title="Dils Wallet API", version="0.1.0")
from fastapi import Response

@app.get("/")
def root_ok():
    return {"ok": True}

@app.head("/")
def root_head():
    return Response(status_code=200)


@app.get("/")
def root_ok():
    return {"ok": True}

app.include_router(api_v1_router)
include_auth_routes(app)  # AURA auth routes
include_daily_routes(app)  # PIX daily-summary
app = FastAPI(title="Dils Wallet API", version="0.1.0")
app.include_router(api_v1_router)
include_daily_routes(app)  # PIX daily-summary routes

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


@app.get("/")
async def root():
    return {"status": "ok", "service": "dils-wallet"}

@app.get("/health")
async def health_root():
    return {"status": "ok", "service": "dils-wallet"}

# Health
@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "dils-wallet"}
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
    # imports tardios para evitar ciclos
    from importlib import import_module
    auth_mod = import_module("backend.app.api.v1.routes.auth")
    refresh_mod = import_module("backend.app.api.v1.routes.refresh")
    users_mod = import_module("backend.app.api.v1.routes.users")
    tx_mod = import_module("backend.app.api.v1.routes.transactions")
    pix_mod = import_module("backend.app.api.v1.routes.pix")
    from backend.app.api.v1.routes import pix_history
    from backend.app.api.v1.routes import pix_summary
    from backend.app.api.v1.routes import pix_stats


_include_routes()

@app.head("/api/v1/health")
def health_head():
    from fastapi import Response
    return Response(status_code=200)
