from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

# Origens que vamos permitir no dev local
ALLOWED = {
    "http://127.0.0.1:5500","http://localhost:5500",
    "http://127.0.0.1:5501","http://localhost:5501",
}

class _HardCORS(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp = await call_next(request)
        origin = request.headers.get("origin")
        if origin in ALLOWED:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Vary"] = (resp.headers.get("Vary","") + ", Origin").strip(", ")
        return resp

def init(app):
    import os
    if os.getenv("CORS_CATCHALL_OPTIONS","0").strip().lower() not in ("1","true","yes","on"):
        return

    # aplica o middleware
    app.add_middleware(_HardCORS)

    # fallback global para preflight OPTIONS
    @app.options("/{rest_of_path:path}")
    async def _opts(rest_of_path: str, request: Request):
        origin = request.headers.get("origin")
        headers = {
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers","*"),
            "Vary": "Origin",
        }
        if origin in ALLOWED:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        return Response(status_code=204, headers=headers)
