from app.utils import db_wait
from app import models
from app.database import Base, engine
from app.routers import ai
from app.routers import summary
from app.routers import pix
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.routers.ai import router as ai_router_legacy
from app.api.v1.routes import ai as ai_router_v1

# App
app = FastAPI(title="Dils Wallet API", version="0.3.0")

# CORS (abrir em dev; ajustar na prod)
origins = [
    "http://localhost:5173","http://127.0.0.1:5173",
    "http://localhost:5174","http://127.0.0.1:5174",
    "http://localhost:5175","http://127.0.0.1:5175",
    "http://localhost:8080","http://127.0.0.1:8080"
]
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
def healthz():
    return {"ok": True, "service": "dils-wallet"}

# Startup: importa models e cria tabelas
@app.on_event("startup")
def on_startup_create_tables():
    try:
        import importlib, pkgutil
        import app.models as _models_pkg
        for m in [m.name for m in pkgutil.iter_modules(_models_pkg.__path__)]:
            importlib.import_module(f"app.models.{m}")
        print("[AUREA DB] models importados (base)")

        from app.database import Base, engine
        Base.metadata.create_all(engine)
        print("[AUREA DB] create_all(Base) OK")
    except Exception as e:
        print("[AUREA DB] erro no create_all(Base):", e)

# Routers
from app.utils.db_wait import wait_and_create_all
import threading

app.include_router(pix.router, prefix="/api/v1/pix", tags=["pix"])
app.include_router(summary.router)
app.include_router(ai_router_legacy)
app.include_router(ai_router_v1.router)
# --- AUREA DB: inicialização assíncrona para não travar healthcheck ---

try:

    threading.Thread(target=wait_and_create_all, args=(Base,), daemon=True).start()

    print("[AUREA DB] wait_and_create_all disparado em background")

except Exception as e:

    print("[AUREA DB] erro ao iniciar thread de init:", e)

# --- END AUREA DB ---

from app.utils.db_wait import wait_and_create_all
print('[AUREA DB] iniciando wait_and_create_all...')
db_wait.wait_and_create_all(Base)

# --- AUREA PATCH: registrar rota de dev para inserir PIX ---
try:
    from app.routers.pix_dev import router as pix_dev_router
    app.include_router(pix_dev_router)
    print("[AUREA DEV] rota /api/v1/pix/_dev_insert registrada")
except Exception as e:
    print("[AUREA DEV] falha ao registrar rota dev:", e)
# --- END PATCH ---

# --- healthcheck leve para o Railway ---
@app.get("/__alive", include_in_schema=False)
def __alive():
    return {"ok": True}

from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DBAPIError

# Fallback: se a rota /api/v1/ai/summary explodir por erro de DB, responde 200 com resumo degradado
@app.exception_handler((OperationalError, DBAPIError, SQLAlchemyError))
async def _db_error_handler(request, exc):
    try:
        path = str(request.url.path)
    except Exception:
        path = ""
    if path.endswith("/api/v1/ai/summary"):
        return JSONResponse(status_code=200, content={
            "saldo_atual": 0.0,
            "entradas_total": 0.0,
            "saidas_total": 0.0,
            "ultimas_24h": {"entradas": 0, "saidas": 0, "qtd": 0},
            "status": "degraded"
        })
    return JSONResponse(status_code=503, content={"error": "db_unavailable"})
