from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import Base, engine

# Routers principais / legados
from app.api.v1.routes import assist as assist_router_v1
from app.routers import pix_send
from app.routers import admin_dbfix
from app.routers import summary
from app.routers import pix
from app.routers.pix_send import router as pix_send_router
from app.api.v1.routes import ai as ai_router_v1
from app.api.v1.routes.ai import router as __ai_router_v1__

# FastAPI app
app = FastAPI(title="Dils Wallet API", version="0.3.0")

# Rotas base
app.include_router(assist_router_v1.router)
app.include_router(pix_send.router)
app.include_router(ai_router_v1.router)

# Bootstrap do ledger PIX
from app.utils.ddl_bootstrap import ensure_pix_ledger
ensure_pix_ledger()

# --- CORS ---
_default_dev = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5174", "http://127.0.0.1:5174",
    "http://localhost:8080", "http://127.0.0.1:8080",
]
origins = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o] or _default_dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Admin / manutenção
app.include_router(admin_dbfix.router, prefix="/admin")

# Healthcheck
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "dils-wallet"}

# OPTIONS global (CORS preflight)
@app.options("/{full_path:path}")
def options_any(full_path: str, request: Request):
    return Response(status_code=204)

# --- AUREA GOLD: rotas PIX Super2 ---
from app.api.v1.routes import pix_balance_get
from app.api.v1.routes import pix_history_get
from app.api.v1.routes import pix_7d

app.include_router(pix_balance_get.router)
app.include_router(pix_history_get.router)
app.include_router(pix_7d.router)

# Execução local
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
