from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from starlette.responses import Response

ALLOWED_ORIGINS = ["http://127.0.0.1:5500", "http://localhost:5500"]

def add_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def include_preflight(app):
    async def _preflight(request: Request, full_path: str = ""):
        origin = request.headers.get("origin") or ""
        allow_origin = origin if origin in ALLOWED_ORIGINS else "*"
        allow_headers = request.headers.get("access-control-request-headers") or "*"
        allow_method  = request.headers.get("access-control-request-method") or "GET"
        headers = {
            "Access-Control-Allow-Origin": allow_origin,
            "Vary": "Origin",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": allow_headers,
            "Access-Control-Allow-Methods": f"{allow_method}, OPTIONS",
            "Access-Control-Max-Age": "86400",
        }
        return Response(status_code=204, headers=headers)

    app.router.add_route("/{full_path:path}", _preflight, methods=["OPTIONS"])
