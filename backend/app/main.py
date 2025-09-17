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
# --- feature flag: transactions router (prod-safe) ---
if os.getenv("ROUTES_TRANSACTIONS", "0") == "1":
    from app.api.v1.routes import transactions
    app.include_router(
        transactions.router,
        prefix="/api/v1/transactions",
        tags=["transactions"],
    )
# --- end flag ---
