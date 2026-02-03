from fastapi import FastAPI
from app.api.v1.routes.auth import router as auth_router

def include_auth_routes(app: FastAPI):
    # O router já tem prefix="/auth", então aqui usamos só "/api/v1"
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

def register_auth(app):
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
