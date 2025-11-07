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
app.include_router(admin_seed.router, prefix="/admin")
