from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.api.v1.routes.auth import get_current_user  # reaproveita função já existente

# só repassa, pra evitar import circular
def get_current_user_dep(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return current_user
