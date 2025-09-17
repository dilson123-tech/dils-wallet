from fastapi import APIRouter

router = APIRouter(prefix="/dev-seed", tags=["dev-seed"])

@router.get("/ping")
def ping_seed():
    return {"ok": True, "seed": True}
