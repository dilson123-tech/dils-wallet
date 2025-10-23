# from app.routers import health
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy.orm import Session
import time

from . import models
from .database import engine, Base, get_db

# cria tabelas automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aurea Gold Backend", version="1.0.0")

@app.get("/healthz")
def healthz():
    """Usado pelo Railway para o Healthcheck"""
    return {"status": "ok", "service": "dils-wallet", "ts": int(time.time())}

@app.get("/")
def root():
    return {"status": "ok", "root": True}

@app.get("/users/test-db")
def test_db(db: Session = Depends(get_db)):
    return {"msg": "DB conectado!"}

# registra health SEM prefixo, após app final
# app.include_router(health.router)
@app.on_event("startup")
async def _log_routes():
    try:
        from logging import getLogger
        log = getLogger("uvicorn")
        paths = [getattr(r, "path", str(r)) for r in app.router.routes]
        log.info(f"[ROUTES] {paths}")
    except Exception:
        pass

# --- FIX: Health real para Railway ---
try:
    @app.get("/healthz", include_in_schema=False)
    def _final_health():
        return {"status": "ok", "service": "dils-wallet", "health": True}
except Exception as e:
    import sys
    print(f"[HEALTH-FIX] falhou ao registrar healthz: {e}", file=sys.stderr)
