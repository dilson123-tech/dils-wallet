import logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO)

import os
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




