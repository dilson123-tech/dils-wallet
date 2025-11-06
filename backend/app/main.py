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

# CORS (abrir em dev; ajustar na prod)
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175,http://localhost:8080,http://127.0.0.1:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static (opcional)
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception:
    pass

# Health
@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "dils-wallet"}

@app.get("/")
async def root():
    return {"status": "ok"}

# Startup: cria tabelas
@app.on_event("startup")
def on_startup_create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("[AUREA DB] create_all(Base) OK")
    except Exception as e:
        print("[AUREA DB] erro no create_all(Base):", e)

# Routers
app.include_router(summary.router)
app.include_router(pix.router)  # legado
app.include_router(pix_send_router, prefix="/api/v1")
