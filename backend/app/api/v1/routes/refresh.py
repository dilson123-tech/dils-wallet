from fastapi import APIRouter

router = APIRouter(prefix="", tags=["auth"])

@router.post("/refresh")
def refresh_stub():
    # rota antiga desativada temporariamente
    return {"detail": "refresh disabled"}
