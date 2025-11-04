from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/api/v1/pix", tags=["pix-dev"])

class DevItem(BaseModel):
    secret: str
    user_id: int = 1
    tipo: str
    valor: float
    descricao: str = ""

@router.post("/_dev_insert")
def dev_insert(item: DevItem, db: Session = Depends(get_db)):
    if item.secret != os.getenv("AUREA_DEV_SECRET"):
        raise HTTPException(status_code=403, detail="forbidden")

    db.execute(text("""
    CREATE TABLE IF NOT EXISTS pix_transactions (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL,
      tipo VARCHAR(16) NOT NULL,
      valor NUMERIC(12,2) NOT NULL,
      descricao TEXT,
      "timestamp" TIMESTAMP DEFAULT now()
    )
    """))

    db.execute(
        text("""
          INSERT INTO pix_transactions (user_id, tipo, valor, descricao)
          VALUES (:user_id, :tipo, :valor, :descricao)
        """),
        dict(user_id=item.user_id, tipo=item.tipo, valor=item.valor, descricao=item.descricao)
    )
    db.commit()
    return {"ok": True}
