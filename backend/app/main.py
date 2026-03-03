from fastapi import FastAPI, Request, HTTPException
from app.api.v1.register_auth import register_auth

def _allow_dev_seed() -> bool:
    return os.getenv("ALLOW_DEV_SEED", "0").strip().lower() in ("1","true","yes","on")

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import os

from app.database import Base, engine
from app.core.rate_limit import init_rate_limiter
from app.core.observability import setup_logging, observability_middleware, metrics_response

# Routers principais / legados
from app.api.v1.routes import assist as assist_router_v1         # módulo com .router
from app.routers import admin_dbfix                              # módulo com .router
from app.api.v1.routes.ai import router as ai_router_v1          # já é APIRouter

# PIX Super2 (nossas rotas novas)
from app.api.v1.routes import pix_balance_get                    # módulo com .router
from app.api.v1.routes.pix import router as pix_router
from app.api.v1.routes import pix_history_get                    # módulo com .router
from app.api.v1.routes import pix_7d
from app.api.v1.routes import pix_forecast_get                             # módulo com .router
from app.routers import dev_seed



# --- Docs/OpenAPI gate (PROD hardening) ---
def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1","true","yes","y","on"}

DOCS_PUBLIC = _env_bool("DOCS_PUBLIC", True)
app = FastAPI(title="Dils Wallet API", version="0.3.0",
    docs_url="/docs" if DOCS_PUBLIC else None,
    redoc_url="/redoc" if DOCS_PUBLIC else None,
    openapi_url="/openapi.json" if DOCS_PUBLIC else None,
)
# Init Rate Limiter
limiter = init_rate_limiter(app)
setup_logging()

@app.get("/")
def root():
    return {"ok": True, "service": "dils-wallet"}


register_auth(app)
# app.include_router(pix_balance_get.router)
app.include_router(pix_router)

# --- Observability (request_id + logs + metrics) ---
@app.middleware("http")
async def aurea_observability(request: Request, call_next):
    return await observability_middleware(request, call_next)
# --- /Observability ---


# --- Routers base ---
app.include_router(assist_router_v1.router)
app.include_router(ai_router_v1)
app.include_router(admin_dbfix.router, prefix="/admin")
app.include_router(dev_seed.router)

from app.api.v1.ai import chat_lab_router
app.include_router(chat_lab_router, prefix="/api/v1/ai")
# --- CORS (hardened) ---
cors_env = os.getenv("CORS_ORIGINS", "").strip()
origins = [o.strip() for o in cors_env.split(",") if o.strip()]

if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],  # origins travadas via CORS_ORIGINS
        expose_headers=["retry-after", "x-request-id"],
        max_age=600,
    )
else:
    print("[CORS] disabled (CORS_ORIGINS vazio)")

# --- Healthcheck ---
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "dils-wallet"}

# --- Readiness (DB) ---
@app.get("/readyz")
def readyz():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True, "service": "dils-wallet", "ready": True}
    except Exception:
        raise HTTPException(status_code=503, detail="db not ready")

# --- Metrics (Prometheus) ---
METRICS_PUBLIC = _env_bool("METRICS_PUBLIC", False)
METRICS_TOKEN = os.getenv("METRICS_TOKEN", "").strip()

@app.get("/metrics")
def metrics(request: Request):
    if METRICS_PUBLIC:
        return metrics_response()
    if METRICS_TOKEN and request.headers.get("X-Metrics-Token") == METRICS_TOKEN:
        return metrics_response()
    raise HTTPException(status_code=404, detail="Not Found")

# --- OPTIONS global (CORS preflight) ---
