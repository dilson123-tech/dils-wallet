from fastapi import FastAPI, Request, Response
from datetime import datetime
from fastapi import Request
import logging
import uuid
import time

from app.api.v1.register_auth import register_auth

def _allow_dev_seed() -> bool:
    return os.getenv("ALLOW_DEV_SEED", "0").strip().lower() in ("1","true","yes","on")

from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import Base, engine

# Routers principais / legados
from app.api.v1.routes import assist as assist_router_v1         # módulo com .router
from app.routers import admin_dbfix                              # módulo com .router
from app.routers.pix_send import router as pix_send_router       # já é APIRouter
from app.api.v1.routes.ai import router as ai_router_v1          # já é APIRouter

# PIX Super2 (nossas rotas novas)
from app.api.v1.routes import pix_balance_get                    # módulo com .router
from app.api.v1.routes import pix_history_get                    # módulo com .router
from app.api.v1.routes import pix_7d
from app.api.v1.routes import pix_forecast_get                             # módulo com .router



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
@app.get("/")
def root():
    return {"ok": True, "service": "dils-wallet"}


register_auth(app)

# --- Request-ID (produção): correlação de logs por chamada ---
logger = logging.getLogger("aurea.request")

@app.middleware("http")
async def aurea_request_id_mw(request: Request, call_next):
    rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        ms = int((time.perf_counter() - start) * 1000)
        logger.exception("rid=%s %s %s -> EXC %sms", rid, request.method, request.url.path, ms)
        raise
    ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Request-Id"] = rid
    logger.info("rid=%s %s %s -> %s %sms", rid, request.method, request.url.path, response.status_code, ms)
    return response
# --- /Request-ID ---

# AUREA_MW_PIXBAL_TRACE
@app.middleware("http")
async def aurea_trace_pix_balance(request: Request, call_next):
    try:
        if request.url.path == "/api/v1/pix/balance":
            auth = request.headers.get("authorization")
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            print("[PIX_BAL_TRACE]",
                  request.method, str(request.url),
                  "auth=" + ("yes" if auth else "no"),
                  "auth_head=" + ((auth[:25] + "...") if auth else "None"),
                  "origin=" + str(origin),
                  "referer=" + str(referer))
    except Exception as e:
        print("[PIX_BAL_TRACE_ERR]", e)
    return await call_next(request)

# --- Routers base ---
app.include_router(assist_router_v1.router)
app.include_router(pix_send_router)
app.include_router(ai_router_v1)
app.include_router(admin_dbfix.router, prefix="/admin")

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
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["retry-after"],
        max_age=600,
    )
else:
    print("[CORS] disabled (CORS_ORIGINS vazio)")

# --- Healthcheck ---
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "dils-wallet"}

# --- OPTIONS global (CORS preflight) ---
