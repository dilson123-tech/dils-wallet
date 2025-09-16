
from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="Dils Wallet API", version="0.1.0")

# ---- healthcheck simples ----
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ---- OpenAPI resiliente (nunca derruba startup) ----
def _safe_openapi():
    try:
        return get_openapi(title="Dils Wallet API", version="0.1.0", routes=app.routes)
    except Exception as e:
        print("WARN: OpenAPI fallback ->", e)
        return {
            "openapi": "3.1.0",
            "info": {"title": "Dils Wallet API", "version": "0.1.0"},
            "paths": {},
        }
app.openapi = _safe_openapi

# ---- includes opcionais (não quebram o boot se falharem) ----
def try_include():
    # AUTH
    try:
        from app.api.v1.routes import auth as auth_routes
        app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])
        print("[routes] auth ON")
    except Exception as e:
        print("[routes] auth OFF ->", e)

    # USERS
    try:
        from app.api.v1.routes import users as users_routes
        app.include_router(users_routes.router, prefix="/api/v1/users", tags=["users"])
        print("[routes] users ON")
    except Exception as e:
        print("[routes] users OFF ->", e)

    # TRANSACTIONS (se não existir modelo/DB, fica OFF sem derrubar nada)
    try:
        from app.api.v1.routes import transactions as tx_routes
        app.include_router(tx_routes.router, prefix="/api/v1/transactions", tags=["transactions"])
        print("[routes] transactions ON")
    except Exception as e:
        print("[routes] transactions OFF ->", e)

    # EXPORT CSV
    try:
        from app.routers import export_csv as export_csv_routes
        app.include_router(export_csv_routes.router)  # já vem com prefix interno
        print("[routes] export_csv ON")
    except Exception as e:
        print("[routes] export_csv OFF ->", e)


    # DEV DB tools
    try:
        from app.routers import dev_db as dev_db_routes
        app.include_router(dev_db_routes.router)
        print("[routes] dev_db ON")
    except Exception as e:
        print("[routes] dev_db OFF ->", e)
try_include()


# --- DB init seguro (cria tabelas se não existirem) ---
try:
    from app.database import Base, engine
    @app.on_event("startup")
    def _init_db_on_startup():
        try:
            Base.metadata.create_all(bind=engine)
            print("[startup] DB create_all OK")
        except Exception as e:
            print("[startup] DB create_all falhou:", e)
except Exception as e:
    print("[startup] DB init não injetado:", e)
# -------------------------------------------------------

# ---- DEBUG: lista de rotas registradas ----
try:
    @app.get("/_routes")
    def _routes():
        try:
            return {
                "count": len(app.routes),
                "routes": [
                    {
                        "path": r.path,
                        "name": getattr(r, "name", None),
                        "methods": sorted(list(getattr(r, "methods", []) or [])),
                        "include_in_schema": getattr(r, "include_in_schema", True),
                    }
                    for r in app.routes
                ],
            }
        except Exception as e:
            return {"error": str(e)}
except Exception as e:
    print("[debug] _routes endpoint não registrado:", e)
# -------------------------------------------
