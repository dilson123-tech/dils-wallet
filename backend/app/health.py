import os
from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException

router = APIRouter()
TOKEN = os.getenv("HEALTH_TOKEN", "")

@router.get("/healthz", include_in_schema=False)
def healthz(x_health_token: str | None = Header(None, convert_underscores=False)):
    if TOKEN:
        if not x_health_token or x_health_token != TOKEN:
            raise HTTPException(status_code=401, detail="unauthorized")
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}
