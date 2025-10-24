from fastapi import APIRouter
from .routes import pix

api_router = APIRouter()

# Inclui o router PIX mock
api_router.include_router(pix.router)

# === include pix_daily router ===
try:
    from app.api.v1.routes.pix_daily import router as pix_daily_router
    api_router.include_router(pix_daily_router, prefix="/pix", tags=["PIX"])
except Exception as e:
    # fallback silencioso em caso de import antes da criação de api_router
    pass
