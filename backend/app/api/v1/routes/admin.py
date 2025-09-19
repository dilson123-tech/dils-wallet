from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text
from app.database import engine
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
        m = getattr(row, "_mapping", row)
        dt = str(m[0]); prec = int(m[1]); scale = int(m[2])
        if dt in ("numeric","decimal") and prec==12 and scale==2:
            return {"status":"noop", "type":dt, "precision":prec, "scale":scale}
        c.execute(text("""
            ALTER TABLE transactions
            ALTER COLUMN valor TYPE numeric(12,2)
            USING ROUND(valor::numeric, 2)
        """))
        c.commit()
        return {"status":"migrated", "to":"numeric(12,2)"}


@router.get("/secret_status")
def secret_status():
    import os
    s = os.getenv("MIGRATE_SECRET")
    return {"loaded": bool(s), "length": len(s) if s else 0}
