from fastapi import APIRouter, Request, Response
from app.cors import ALLOWED_ORIGINS

router = APIRouter()

@router.options("/{full_path:path}")
def preflight(full_path: str, request: Request):
    origin = request.headers.get("origin", "")
    headers = request.headers.get("access-control-request-headers", "*")

    resp = Response(status_code=204)
    if origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Methods"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = headers or "*"
    return resp
