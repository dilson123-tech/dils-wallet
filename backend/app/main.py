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
origins = ["*"]  # dev livre; depois a gente fecha pra produção

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
# -----------------------------------------------------------------------------

# PIX (painel financeiro, histórico e saldo)
pix_router = importlib.import_module("app.routers.pix").router
app.include_router(pix_router, prefix="/api/v1/pix", tags=["pix"])

# IA 3.0 (concierge Aurea)
app.include_router(ai_router.router, prefix="/api/v1", tags=["ai"])
from app.routers import ai
app.include_router(ai.router)
