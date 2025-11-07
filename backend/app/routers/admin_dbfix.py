from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.post("/db_fix_pix_desc_trigger")
def db_fix_pix_desc_trigger(db: Session = Depends(get_db)):
    try:
        # função que força descricao = '' quando vier NULL
        db.execute(text("""
            CREATE OR REPLACE FUNCTION pix_tx_desc_not_null()
            RETURNS trigger AS $$
            BEGIN
                IF NEW.descricao IS NULL THEN
                    NEW.descricao := '';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        # recria o trigger
        db.execute(text("DROP TRIGGER IF EXISTS pix_tx_desc_nn ON pix_transactions;"))
        db.execute(text("""
            CREATE TRIGGER pix_tx_desc_nn
            BEFORE INSERT ON pix_transactions
            FOR EACH ROW EXECUTE FUNCTION pix_tx_desc_not_null();
        """))
        # corrige linhas antigas, se houver
        db.execute(text("UPDATE pix_transactions SET descricao = '' WHERE descricao IS NULL;"))
        db.commit()
        return {"ok": True, "fix": "pix_tx_desc_nn installed"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"db_fix_failed: {e}")
