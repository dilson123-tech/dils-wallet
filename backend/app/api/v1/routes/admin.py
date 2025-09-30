from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text
from .database import engine
import os

router = APIRouter()

@router.post("/migrate_decimal")
def migrate_decimal(x_admin_secret: str | None = Header(None, alias="X-Admin-Secret")):
    secret = os.getenv("MIGRATE_SECRET")
    if not secret or x_admin_secret != secret:
        raise HTTPException(status_code=401, detail="unauthorized")

    with engine.connect() as c:
        dia = c.dialect.name
        if dia != "postgresql":
            return {"status": "skipped", "dialect": dia}

        row = c.execute(text("""
            select data_type, numeric_precision, numeric_scale
            from information_schema.columns
            where table_name='transactions' and column_name='valor'
        """)).fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="transactions.valor not found")

        try:
            m = row._mapping  # SQLA 1.4/2.0
            dt = str(m["data_type"])
            prec = int(m["numeric_precision"]) if m["numeric_precision"] is not None else 0
            scale = int(m["numeric_scale"]) if m["numeric_scale"] is not None else 0
        except Exception:
            dt, prec, scale = str(row[0]), int(row[1] or 0), int(row[2] or 0)

        if dt in ("numeric", "decimal") and prec == 12 and scale == 2:
            return {"status": "noop", "type": dt, "precision": prec, "scale": scale}

        c.execute(text("""
            ALTER TABLE transactions
            ALTER COLUMN valor TYPE numeric(12,2)
            USING ROUND(valor::numeric, 2)
        """))
        c.commit()
        return {"status": "migrated", "to": "numeric(12,2)"}

@router.get("/secret_status")
def secret_status():
    s = os.getenv("MIGRATE_SECRET")
    return {"loaded": bool(s), "length": len(s) if s else 0}
