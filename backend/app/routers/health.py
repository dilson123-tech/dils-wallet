from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.database import get_db

router = APIRouter(tags=["health"])

@router.get("/healthz")
def healthz(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"ok": True, "db": "up"}
    except Exception:
        return {"ok": False, "db": "down"}
