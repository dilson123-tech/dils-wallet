from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

# carrega app real (se existir)
try:
    from app import main as _main
    _real = getattr(_main, "app", None) or getattr(_main, "api", None) or getattr(_main, "application", None)
    if not isinstance(_real, FastAPI):
        _real = FastAPI(title="Aurea Fallback")
except Exception:
    _real = FastAPI(title="Aurea Fallback (import fail)")

async def _health(_req): return JSONResponse({"ok": True, "service": "dils-wallet"})
async def _root(_req):   return JSONResponse({"ok": True, "root": True})

# ordem importa: rotas fixas primeiro, depois montamos o app real
app = Starlette(
    routes=[
        Route("/healthz", _health),   # sempre 200
        Route("/", _root),            # sempre 200
        Mount("/", app=_real),        # todo o resto vai pro app real
    ]
)

import sys
print(f"[ENTRYPOINT/WRAPPER] mounted real app={type(_real)}", file=sys.stderr)

from app.api.v1.routes import ai as ai_routes
app.include_router(ai_routes.router, prefix="/api/v1/ai")
