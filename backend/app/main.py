from fastapi.responses import Response
from app.routers import export_csv as export_csv_routes
from app.api.v1.routes import transactions as transactions_routes
from app.api.v1.routes import users as users_routes
from app.api.v1.routes import auth as auth_routes
from prometheus_fastapi_instrumentator import Instrumentator
from pythonjsonlogger import jsonlogger
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from app.core.db import get_db
from fastapi import Response
from app.routers import dev as dev_router
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import time

from . import models
from .database import engine, Base, get_db

# Criar as tabelas automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dils Wallet API", version="0.1.0", docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")






# --- include resiliente para export_csv ---
try:
    from app.routers import export_csv as _export_csv_mod
    if hasattr(_export_csv_mod, "router"):
        app.include_router(_export_csv_mod.router)
    elif hasattr(_export_csv_mod, "export_csv"):
        app.add_api_route("/api/v1/transactions/export.csv", _export_csv_mod.export_csv, methods=["GET"], tags=["transactions"])
    else:
        print("WARN: export_csv sem router nem função export_csv; ignorando.")
except Exception as e:
    print("WARN: falha ao carregar export_csv:", e)
# --- fim include resiliente ---

# --- OpenAPI resiliente: evita 502 se schema quebrar ---
_openapi_cache = None
def custom_openapi():
    global _openapi_cache
    if _openapi_cache:
        return _openapi_cache
    try:
        _openapi_cache = get_openapi(
            title=getattr(app, "title", "Dils Wallet API"),
            version="0.1.0",
            routes=app.routes,
        )
    except Exception as e:
        # Fallback mínimo, mas válido
        _openapi_cache = {
            "openapi": "3.1.0",
            "info": {"title": getattr(app, "title", "Dils Wallet API"), "version": "0.1.0"},
            "paths": {},
        }
    return _openapi_cache

app.openapi = custom_openapi
# --- fim OpenAPI resiliente ---

DOCS_PATHS = {"/docs", "/redoc"}

@app.middleware("http")
async def csp_for_docs(request: Request, call_next):
    resp: Response = await call_next(request)
    if request.url.path in DOCS_PATHS:
        resp.headers["content-security-policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' https://cdn.jsdelivr.net"
        )
    return resp

# === Routers v1 ===
try:
    app.include_router(auth_routes.router,        prefix="/api/v1/auth")
    app.include_router(users_routes.router,       prefix="/api/v1/users")
    app.include_router(transactions_routes.router,prefix="/api/v1/transactions")
    app.include_router(export_csv_routes.router)  # já vem com prefix /api/v1/transactions
except Exception as e:
    print("[router-include] warn:", e)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dev_router.router)

from app.routers import export_csv
# DISABLED DUP: app.include_router(export_csv.router)
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

from app.routers.transactions import router as transactions_router
# DISABLED DUP: app.include_router(transactions_router)

from app.routers.dev_seed import router as dev_router
app.include_router(dev_router)

# --- logging JSON ---
_handler = logging.StreamHandler()
_handler.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
logging.getLogger().handlers = [_handler]
logging.getLogger().setLevel(logging.INFO)

# --- Prometheus metrics ---
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


# --- Security headers (safe) ---
@app.middleware("http")
async def security_headers_safe(request, call_next):
    response = await call_next(request)
    headers = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:",
    }
    for k, v in headers.items():
        # não sobrescreve se já existir
        if k not in response.headers:
            response.headers[k] = v
    return response
