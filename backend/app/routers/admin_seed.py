from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.post("/seed_user")
def seed_user(db: Session = Depends(get_db)):
    try:
        db.execute(text(
            "INSERT INTO users (username, hashed_password, role) "
            "VALUES ('admin@aurea.local','seed-placeholder','admin') "
            "ON CONFLICT DO NOTHING"
        ))
        db.commit()
        return {"ok": True, "seeded": "admin@aurea.local"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"seed_failed: {e}")
