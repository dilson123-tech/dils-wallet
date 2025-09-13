
from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="Dils Wallet API", version="0.1.0")

# --- healthcheck SEMPRE disponível ---
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# --- OpenAPI com fallback: nunca derruba startup ---
def _safe_openapi():
    try:
        return get_openapi(title="Dils Wallet API", version="0.1.0", routes=app.routes)
    except Exception as e:
        print("WARN: OpenAPI fallback ->", e)
        return {"openapi": "3.1.0", "info": {"title": "Dils Wallet API", "version": "0.1.0"}, "paths": {}}
app.openapi = _safe_openapi

# --- Include OPCIONAL de rotas pesadas (nunca quebram o boot) ---
def _try_include():
    # transactions (opcional)
    try:
        from app.api.v1.routes import transactions as tx_routes
        app.include_router(tx_routes.router, prefix="/api/v1/transactions", tags=["transactions"])
        print("[routes] transactions ON")
    except Exception as e:
        print("[routes] transactions OFF ->", e)

    # export_csv (opcional)
    try:
        from app.routers import export_csv as export_csv_routes
        app.include_router(export_csv_routes.router)
        print("[routes] export_csv ON")
    except Exception as e:
        print("[routes] export_csv OFF ->", e)

_try_include()
