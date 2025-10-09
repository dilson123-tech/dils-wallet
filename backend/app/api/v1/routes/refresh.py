from fastapi import APIRouter

router = APIRouter(tags=["refresh"])

@router.post("/")
def refresh_stub():
    # rota antiga desativada temporariamente
    return {"detail": "refresh disabled"}
