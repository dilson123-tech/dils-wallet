from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter, Request
from starlette.responses import Response

ALLOWED_ORIGINS = ["http://127.0.0.1:5500", "http://localhost:5500"]

def add_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

def include_preflight(app):
    router = APIRouter()

    @router.options("/{rest_of_path:path}")
    async def preflight(rest_of_path: str, request: Request):
        origin = request.headers.get("origin", "")
        allow_origin = origin if origin in ALLOWED_ORIGINS else "*"
        allow_headers = request.headers.get("access-control-request-headers", "*")
        allow_method = request.headers.get("access-control-request-method", "GET")
        resp = Response(status_code=204)
        resp.headers.update({
            "Access-Control-Allow-Origin": allow_origin,
            "Vary": "Origin",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": allow_headers,
            "Access-Control-Allow-Methods": f"{allow_method}, OPTIONS",
            "Access-Control-Max-Age": "86400",
        })
        return resp

    app.include_router(router)
