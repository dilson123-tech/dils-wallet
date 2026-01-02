from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.pix_tx import get_pix_context

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

@router.get("/summary")
@router.post("/summary")
def summary_talkback(hours: int = 24, db: Session = Depends(get_db)):
    """
    Resumo rápido do PIX (compatível com o cliente Aurea Gold)
    """
    try:
        resumo = get_pix_context(db, hours)
        return {"ok": True, "summary": resumo, "hours": hours}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no resumo: {e}")
