from fastapi import FastAPI
from .routes.auth import router as auth_router

def include_auth_routes(app: FastAPI):
    app.include_router(auth_router, prefix="/api/v1")
