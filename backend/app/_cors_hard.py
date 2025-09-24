from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

ALLOWED_ORIGINS = {"http://127.0.0.1:5501", "http://localhost:5501"}

class HardCORS(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        allowed = origin in ALLOWED_ORIGINS
        if request.method == "OPTIONS":
            resp = Response(status_code=204)
        else:
            resp = await call_next(request)
        if allowed and origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
            req_hdrs = request.headers.get("access-control-request-headers")
            resp.headers["Access-Control-Allow-Headers"] = req_hdrs or "authorization, content-type"
        return resp
