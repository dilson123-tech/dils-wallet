from fastapi import Response
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import time

from . import models
from .database import engine, Base, get_db

# Criar as tabelas automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dils Wallet API", version="0.1.0")

from app.routers import export_csv
app.include_router(export_csv.router)
from pathlib import Path
UI_DIR = (Path(__file__).resolve().parents[1] / "ui")
app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")
@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


# CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers

@app.get("/healthz")
def healthz():
    return {"status": "ok", "ts": int(time.time())}

@app.get("/users/test-db")
def test_db(db: Session = Depends(get_db)):
    return {"msg": "DB conectado!"}

# --- inclui routers manualmente sem __init__.py para evitar ciclo ---
import importlib
auth_routes = importlib.import_module("app.api.v1.routes.auth")
users_routes = importlib.import_module("app.api.v1.routes.users")
transactions_routes = importlib.import_module("app.api.v1.routes.transactions")

# -------------------------------------------------------------------

# === Routers v1 (carregados sem __init__ p/ evitar ciclo) ===
import importlib
_auth = importlib.import_module("app.api.v1.routes.auth")
_users = importlib.import_module("app.api.v1.routes.users")
_tx = importlib.import_module("app.api.v1.routes.transactions")

app.include_router(_auth.router,  prefix="/api/v1/auth",         tags=["auth"])
app.include_router(_users.router, prefix="/api/v1/users",        tags=["users"])
app.include_router(_tx.router,    prefix="/api/v1/transactions", tags=["transactions"])
# ============================================================

# === Observabilidade mínima (logs JSON + request_id) ===
from app.observability import setup_logging, RequestContextMiddleware  # type: ignore
setup_logging("INFO")
app.add_middleware(RequestContextMiddleware)
# =======================================================

# === Security headers (básico) ===
from app.security_headers import SecurityHeadersMiddleware  # type: ignore
app.add_middleware(SecurityHeadersMiddleware)
# =================================

# === Rate limiting (básico em memória) ===
from app.rate_limit import RateLimitMiddleware  # type: ignore
# capacidade=20 req por 10s por IP+rota (ajuste se quiser)
app.add_middleware(RateLimitMiddleware, capacity=20, refill_time_s=10)
# =========================================

# === Observabilidade externa (Sentry) ===
from app.sentry_init import setup_sentry  # type: ignore
setup_sentry()
# ========================================

# === Rota de debug do Sentry ===
@app.get("/debug-sentry")
def debug_sentry():
    1 / 0  # força ZeroDivisionError
# =================================
