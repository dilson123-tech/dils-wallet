from fastapi import APIRouter

router = APIRouter(prefix="/dev", tags=["dev"])

@router.get("/ping")
def ping():
    return {"ok": True, "pong": True}
