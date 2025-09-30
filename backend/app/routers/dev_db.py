from fastapi import APIRouter, Depends
from sqlalchemy import text
from .database import get_db
import os

router = APIRouter(prefix="/dev", tags=["dev"])

@router.get("/db-ping")
def db_ping(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/env-lite")
def env_lite():
    # não expõe secrets; só presença/ausência
    return {
        "has_DATABASE_URL": bool(os.getenv("DATABASE_URL")),
        "db_url_scheme": (os.getenv("DATABASE_URL","").split("://",1)[0] if os.getenv("DATABASE_URL") else None),
    }
