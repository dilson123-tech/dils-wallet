from fastapi import APIRouter
from .routes import pix

api_router = APIRouter()

# Inclui o router PIX mock
api_router.include_router(pix.router)
