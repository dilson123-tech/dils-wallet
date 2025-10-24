from fastapi import APIRouter

router = APIRouter()

@router.get("/livez")
def livez():
    return {"status": "ok", "service": "dils-wallet"}
