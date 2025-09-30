from backend.app.api.v1.routes.security import get_current_user
from .api.v1.routes import auth
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .... import schemas, database, models

router = APIRouter()

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
