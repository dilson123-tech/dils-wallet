from fastapi import FastAPI
from .routes.pix_daily import router as pix_daily_router

def include_daily_routes(app: FastAPI):
    app.include_router(pix_daily_router, prefix="/api/v1")
