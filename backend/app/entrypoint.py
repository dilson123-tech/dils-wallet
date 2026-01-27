from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount


def _truthy(v: str | None) -> bool:
    if v is None:
        return False
    return v.strip().lower() in {"1", "true", "yes", "on"}


# carrega app real (se existir)
try:
    from app import main as _main  # noqa: F401
    _real = getattr(_main, "app", None) or getattr(_main, "api", None) or getattr(_main, "application", None)
    if not isinstance(_real, FastAPI):
        _real = FastAPI(title="Aurea Fallback")
except Exception as e:
    print(f"[ENTRYPOINT/WRAPPER] import app.main failed: {e}", file=sys.stderr)
    _real = FastAPI(title="Aurea Fallback (import fail)")


def _boot_init_db() -> None:
    # default ON, pq é idempotente e evita 500 por tabela inexistente
    if not _truthy(os.getenv("AUREA_INIT_DB_ON_BOOT", "1")):
        print("[ENTRYPOINT/WRAPPER] init_db disabled", file=sys.stderr)
        return

    from app.utils.init_db import main as _init_db_main
    _init_db_main()
    print("[ENTRYPOINT/WRAPPER] init_db OK ✅", file=sys.stderr)


@asynccontextmanager
async def lifespan(_app: Starlette):
    try:
        _boot_init_db()
    except Exception as e:
        print(f"[ENTRYPOINT/WRAPPER] init_db FAILED: {e}", file=sys.stderr)
        raise
    yield


async def _health(_req):
    return JSONResponse({"ok": True, "service": "dils-wallet"})


async def _root(_req):
    return JSONResponse({"ok": True, "root": True})


# ordem importa: rotas fixas primeiro, depois montamos o app real
app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/healthz", _health, methods=["GET"]),  # sempre 200 se subiu
        Route("/", _root, methods=["GET"]),           # sempre 200
        Mount("/", app=_real),                        # todo o resto vai pro app real
    ],
)

print(f"[ENTRYPOINT/WRAPPER] mounted real app={type(_real)}", file=sys.stderr)

# --- attach AI router defensively (works with wrapper) ---
try:
    from app.api.v1.routes import ai as ai_routes  # noqa: F401
    if hasattr(_real, "include_router"):
        _real.include_router(ai_routes.router, prefix="/api/v1/ai")
except Exception as e:
    print(f"[ENTRYPOINT/WRAPPER] AI router attach skipped: {e}", file=sys.stderr)
