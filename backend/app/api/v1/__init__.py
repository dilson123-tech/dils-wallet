from fastapi import APIRouter
router = APIRouter(prefix="/api/v1")
def _try_include(modpath: str):
    try:
        mod = __import__(modpath, fromlist=["router"])
        router.include_router(getattr(mod, "router"))
    except Exception:
        pass
_try_include("backend.app.api.v1.routes.auth")
_try_include("backend.app.api.v1.routes.users")
_try_include("backend.app.api.v1.routes.pix")
_try_include("backend.app.api.v1.routes.transactions")
_try_include("backend.app.api.v1.routes.health")
