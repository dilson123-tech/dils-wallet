from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = {"http://127.0.0.1:5500", "http://localhost:5500"}

def add_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(ALLOWED_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[],
        max_age=86400,
    )

def attach_options_fallback(app):
    # Responde qualquer OPTIONS com 204 e cabeçalhos CORS (para garantir)
    @app.options("/{full_path:path}")
    async def _options_fallback(full_path: str, request: Request):
        origin = request.headers.get("origin", "")
        acrm = request.headers.get("access-control-request-method", "")
        acrh = request.headers.get("access-control-request-headers", "")
        headers = {}
        if origin in ALLOWED_ORIGINS:
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Vary": "Origin",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": acrm or "GET,POST,PUT,PATCH,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": acrh or "*",
                "Access-Control-Max-Age": "86400",
            }
        return Response(status_code=204, headers=headers)
