from app.api.v1.routes import assist as assist_router_v1
from app.routers import pix_send
from app.api.v1.routes.ai import router as __ai_router_v1__
from app.routers import admin_dbfix
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import Base, engine

# Routers
from app.routers import summary
from app.routers import pix
from app.routers.pix_send import router as pix_send_router

from app.api.v1.routes import ai as ai_router_v1
app = FastAPI(title="Dils Wallet API", version="0.3.0")
app.include_router(assist_router_v1.router)
app.include_router(pix_send.router)
app.include_router(ai_router_v1.router)
from app.utils.ddl_bootstrap import ensure_pix_ledger
ensure_pix_ledger()

# --- CORS robusto ---
_default_dev = [
    "http://localhost:5173","http://127.0.0.1:5173",
    "http://localhost:5174","http://127.0.0.1:5174",
    "http://localhost:8080","http://127.0.0.1:8080",
]
origins = [o for o in os.getenv("CORS_ORIGINS","").split(",") if o] or _default_dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.include_router(admin_dbfix.router, prefix="/admin")

@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "dils-wallet"}


# --- FIX HEALTHCHECK PORT BIND ---
import os, uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
# --- END FIX ---


# --- OPTIONS preflight global ---
@app.options("/{full_path:path}")
def options_any(full_path: str, request: Request):
    return Response(status_code=204)

# --- AUREA GOLD: rota GET /api/v1/pix/balance (super2) ---
from app.api.v1.routes import pix_balance_get
app.include_router(pix_balance_get.router)

# --- AUREA GOLD: rota GET /api/v1/pix/balance (super2) ---
from app.api.v1.routes import pix_balance_get
app.include_router(pix_balance_get.router)

# --- AUREA GOLD: rota PIX /api/v1/pix/7d (todas transações últimos 7 dias) ---
from app.api.v1.routes import pix_7d
app.include_router(pix_7d.router)
