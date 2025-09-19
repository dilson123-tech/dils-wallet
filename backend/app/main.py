import logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO)

import os
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# importa o router do auth
from app.api.v1.routes import auth as auth_routes

app = FastAPI(title="Dils Wallet API", version="0.1.0")

@app.get("/healthz")
def health():
    return {"status": "ok"}

# canário simples direto no main (prova de vida do arquivo em prod)
@app.get("/canary/auth/ping")
def canary():
    return {"ping": "pong", "file": __file__}

# monta o router de auth SEM condições
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])

# (opcional) OpenAPI estável
def _openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    app.openapi_schema = schema
    return app.openapi_schema
app.openapi = _openapi

from app.api.v1.routes import transactions
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])

# --- feature flag: transactions (robusto) ---
def _env_on(name: str) -> bool:
    return os.getenv(name, "0").strip().lower() in {"1","true","on","yes","y"}

logging.getLogger("startup").info("ROUTES_TRANSACTIONS=%s", os.getenv("ROUTES_TRANSACTIONS"))

if _env_on("ROUTES_TRANSACTIONS"):
    try:
        from importlib import import_module
        transactions = import_module("app.api.v1.routes.transactions")
        app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
        logging.getLogger("startup").info("transactions router ENABLED")
    except Exception as e:
        logging.getLogger("startup").exception("failed to enable transactions router: %s", e)
else:
    logging.getLogger("startup").info("transactions router DISABLED")
# --- end flag ---






# CORS configurável por env: CORS_ALLOW_ORIGINS="https://app.seudominio.com,https://www.seuoutro.com"
_allow = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [o.strip() for o in _allow.split(",")] if _allow else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    allow_headers=["Authorization","Content-Type","Accept","Origin","X-Requested-With"],
)



@app.middleware("http")
async def _security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    # HSTS só faz sentido sob HTTPS (Railway usa HTTPS na borda)
    resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    # Trava APIs do navegador que não precisamos
    resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return resp



# --- lightweight metrics (Prometheus-like) ---
from collections import defaultdict
from fastapi import Request
from fastapi.responses import PlainTextResponse

if not hasattr(app.state, "metrics"):
    app.state.metrics = {
        "requests_total": 0,
        "by_status": defaultdict(int),
    }

@app.middleware("http")
async def _metrics_mw(request: Request, call_next):
    resp = await call_next(request)
    try:
        app.state.metrics["requests_total"] += 1
        app.state.metrics["by_status"][str(resp.status_code)] += 1
    except Exception:
        pass
    return resp

@app.get("/metrics")
def metrics():
    m = app.state.metrics
    lines = []
    lines.append("# TYPE app_requests_total counter")
    lines.append(f"app_requests_total {m['requests_total']}")
    lines.append("# TYPE app_requests_status_total counter")
    for k,v in sorted(m["by_status"].items()):
        lines.append(f'app_requests_status_total{{status="{k}"}} {v}')
    body = "\n".join(lines) + "\n"
    return PlainTextResponse(body, media_type="text/plain")
# --- /metrics ---






app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
