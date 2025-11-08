from app.routers import admin_dbfix
from app.routers import admin_seed
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import Base, engine

# Routers
from app.routers import summary
from app.routers import pix
from app.routers.pix_send import router as pix_send_router

app = FastAPI(title="Dils Wallet API", version="0.3.0")

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
app.include_router(pix_send_router, prefix="/api/v1")

@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "dils-wallet"}

app.include_router(admin_seed.router, prefix="/admin")

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
