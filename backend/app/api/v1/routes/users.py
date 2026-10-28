from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.authz import get_current_user, require_admin
from app.models import User

router = APIRouter()

@router.get("/api/v1/users/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": getattr(current_user, "email", None),
        "full_name": getattr(current_user, "full_name", None),
        "role": current_user.role,
    }

@router.get("/api/v1/admin/users", dependencies=[Depends(require_admin)])
def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # somente leitura; allowlist explícita de campos (nunca hash/senha/token)
    total = db.query(User).count()
    users = db.query(User).order_by(User.id).offset(skip).limit(limit).all()
    return {
        "items": [
            {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role}
            for u in users
        ],
        "total": total,
    }
