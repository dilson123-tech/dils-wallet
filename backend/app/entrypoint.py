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


# --- attach AI router defensively (works with wrapper) ---
try:
    from app.api.v1.routes import ai as ai_routes  # noqa: F401
    if 'app' in globals() and hasattr(app, 'include_router'):
        app.include_router(ai_routes.router, prefix="/api/v1/ai")
    elif '_real' in globals() and hasattr(_real, 'include_router'):
        _real.include_router(ai_routes.router, prefix="/api/v1/ai")
    else:
        print("[ENTRYPOINT/WRAPPER] AI router: app not ready, skipping")
except Exception as e:
    print(f"[ENTRYPOINT/WRAPPER] AI router attach skipped: {e}")
# --- end attach ---
