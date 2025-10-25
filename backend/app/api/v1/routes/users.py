from fastapi import APIRouter, Depends
from app.utils.authz import get_current_user, require_admin
from app.models import User

router = APIRouter()

@router.get("/api/v1/users/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }

@router.get("/api/v1/admin/users", dependencies=[Depends(require_admin)])
def admin_list_users():
    # placeholder seguro; depois a gente faz query real
    return {"status": "ok", "message": "área admin liberada"}
