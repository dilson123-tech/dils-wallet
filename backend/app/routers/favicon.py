from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

FAVICON_PATH = Path(__file__).resolve().parents[1] / "ui" / "favicon.ico"

@router.get("/favicon.ico", include_in_schema=False)
def favicon():
    if FAVICON_PATH.exists():
        return FileResponse(FAVICON_PATH)
    return Response(status_code=404)
