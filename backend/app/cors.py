ALLOWED_ORIGINS = ["http://127.0.0.1:5500","http://localhost:5500"]
from fastapi.middleware.cors import CORSMiddleware

def add_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

from fastapi import APIRouter, Request, Response

def include_preflight(app):
    router = APIRouter()

    @router.options("/{full_path:path}")
    def any_options(full_path: str, request: Request):
        origin = request.headers.get("origin", "")
        # Só espelha se estiver permitido
        if origin in ALLOWED_ORIGINS:
            resp = Response(status_code=204)
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Headers"] = request.headers.get(
                "access-control-request-headers", "*"
            )
            method = request.headers.get("access-control-request-method", "GET")
            resp.headers["Access-Control-Allow-Methods"] = f"{method}, OPTIONS"
            return resp
        # Mesmo sem origin válido, responde 204 pra não derrubar o browser
        return Response(status_code=204)

    app.include_router(router)
