from fastapi import Depends
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .api.v1.routes.auth import get_current_user  # reaproveita função já existente

# só repassa, pra evitar import circular
def get_current_user_dep(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return current_user
