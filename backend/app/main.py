from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine
from app.models import Base
import importlib

# importa nosso router de IA 3.0
from app.api.v1.routes import ai as ai_router

# -----------------------------------------------------------------------------
# APP CORE
# -----------------------------------------------------------------------------
app = FastAPI(title="Dils Wallet API", version="0.3.0")

# -----------------------------------------------------------------------------
# BANCO
# -----------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------------------------
# CORS GLOBAL
# -----------------------------------------------------------------------------
origins = [
    "http://localhost:5173","http://127.0.0.1:5173",
    "http://localhost:5174","http://127.0.0.1:5174",
    "http://localhost:5175","http://127.0.0.1:5175",
    "http://localhost:8080","http://127.0.0.1:8080"
]  # dev livre; depois a gente fecha pra produção

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# STATIC FILES (opcional)
# -----------------------------------------------------------------------------
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception:
    pass

# -----------------------------------------------------------------------------
# HEALTHCHECK
# -----------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "dils-wallet"}

# -----------------------------------------------------------------------------
# ROUTERS

# PIX (painel financeiro, histórico e saldo)
from app.routers import pix

# IA 3.0 (concierge Aurea)
from app.routers.ai import router as ai_router
from app.routers import summary

app.include_router(pix.router, prefix="/api/v1/pix", tags=["pix"])
app.include_router(summary.router)
app.include_router(ai_router)
