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
app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")
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
