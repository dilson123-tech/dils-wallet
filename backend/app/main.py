from app.routers import ai

import importlib, pkgutil
from app.database import Base, engine

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
origins = [
    "http://localhost:5173","http://127.0.0.1:5173",
    "http://localhost:5174","http://127.0.0.1:5174",
    "http://localhost:5175","http://127.0.0.1:5175",
    "http://localhost:8080","http://127.0.0.1:8080"
]  # dev livre; depois a gente fecha pra produção

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

# PIX (painel financeiro, histórico e saldo)
from app.routers import pix

# IA 3.0 (concierge Aurea)
from app.routers.ai import router as ai_router
from app.routers import summary

app.include_router(pix.router, prefix="/api/v1/pix", tags=["pix"])
app.include_router(summary.router)
app.include_router(ai_router)
app.include_router(ai.router)


def _aurea_import_all_models():
    try:
        import app.models as _models_pkg
        for m in [m.name for m in pkgutil.iter_modules(_models_pkg.__path__)]:
            importlib.import_module(f"app.models.{m}")
        print("[AUREA DB] models importados")
    except Exception as e:
        print("[AUREA DB] falha ao importar models:", e)

        print("[AUREA DB] create_all OK")
    except Exception as e:
        print("[AUREA DB] create_all falhou:", e)

    try:
        import importlib, pkgutil
        import app.models as _models_pkg
        for m in [m.name for m in pkgutil.iter_modules(_models_pkg.__path__)]:
            importlib.import_module(f"app.models.{m}")
        print("[AUREA DB] models importados")
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("[AUREA DB] create_all OK")
    except Exception as e:
        print("[AUREA DB] erro ao criar tabelas:", e)

@app.on_event("startup")
def on_startup_create_tables():
    import importlib, pkgutil, sys
    from sqlalchemy.orm import DeclarativeMeta
    from app.database import engine

    try:
        # 1) importa todos submódulos de app.models
        try:
            import app.models as _models_pkg
            for m in [m.name for m in pkgutil.iter_modules(_models_pkg.__path__)]:
                importlib.import_module(f"app.models.{m}")
            print("[AUREA DB] models importados")
        except Exception as e:
            print("[AUREA DB] falha ao importar models:", e)

        # 2) coleta TODOS os metadados expostos pelos módulos importados
        metadatas = set()
        for name, mod in list(sys.modules.items()):
            if not name.startswith("app.models."):
                continue
            try:
                for attr_name, obj in vars(mod).items():
                    md = getattr(obj, "metadata", None)
                    if md is not None and hasattr(md, "create_all"):
                        metadatas.add(md)
            except Exception:
                pass

        # fallback: tenta também o Base padrão
        try:
            from app.database import Base as DefaultBase
            metadatas.add(DefaultBase.metadata)
        except Exception:
            pass

        # 3) executa create_all em cada metadata única
        for md in metadatas:
            try:
                md.create_all(bind=engine)
            except Exception as e:
                print("[AUREA DB] erro em create_all(metadata):", e)

        print(f"[AUREA DB] create_all concluído em {len(metadatas)} metadata(s)")
    except Exception as e:
        print("[AUREA DB] erro geral no startup:", e)

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

