import os
from fastapi import APIRouter, HTTPException
from sqlalchemy import inspect
from app.database import engine

router = APIRouter()

@router.get("/db", include_in_schema=False)
def debug_db():
    if os.getenv("DEBUG_DB", "").lower() not in ("1", "true", "yes"):
        raise HTTPException(status_code=404, detail="debug disabled")
    insp = inspect(engine)
    return {
        "engine": engine.url.render_as_string(hide_password=True),
        "tables": insp.get_table_names(),
    }
