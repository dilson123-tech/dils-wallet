import time
print("[AUREA STARTUP] aguardando serviços subirem...")
time.sleep(10)
print("[AUREA STARTUP] iniciando FastAPI normalmente")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Routers
from app.routers import pix, summary
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
app.include_router(pix.router, prefix="/api/v1/pix", tags=["pix"])
app.include_router(summary.router)
app.include_router(ai_router_legacy)
app.include_router(ai_router_v1.router)

from app.utils.db_wait import wait_and_create_all
print('[AUREA DB] iniciando wait_and_create_all...')
wait_and_create_all(Base)

# --- AUREA PATCH: registrar rota de dev para inserir PIX ---
try:
    from app.routers.pix_dev import router as pix_dev_router
    app.include_router(pix_dev_router)
    print("[AUREA DEV] rota /api/v1/pix/_dev_insert registrada")
except Exception as e:
    print("[AUREA DEV] falha ao registrar rota dev:", e)
# --- END PATCH ---
