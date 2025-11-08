from app.routers import admin_dbfix
from app.routers import admin_seed
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import Base, engine

# Routers
from app.routers import summary
from app.routers import pix
from app.routers.pix_send import router as pix_send_router

app = FastAPI(title="Dils Wallet API", version="0.3.0")
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
