from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.pix_transaction import PixTransaction

router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])

def _pick_date_col():
    # escolhe automaticamente a coluna de data existente no model
    candidates = ["created_at", "created", "timestamp", "data", "dia", "date"]
    cols = set(PixTransaction.__table__.columns.keys())
    for name in candidates:
        if name in cols:
            return getattr(PixTransaction, name)
    return None

DATE_COL = _pick_date_col()

@router.get("/history")
def get_pix_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    """
    Retorna histórico PIX:
    - history: transações cruas
    - dias: resumo por dia (entradas/saídas)
    """
    q = db.query(PixTransaction)

    # se o model tiver campo email, filtra (safe)
    if x_user_email and "email" in PixTransaction.__table__.columns.keys():
        q = q.filter(PixTransaction.email == x_user_email)

    if DATE_COL is not None:
        q = q.order_by(DATE_COL.desc())

    transactions = q.offset(offset).limit(limit).all()

    # resumo diário
    dias_map = {}
    for t in transactions:
        # pega a data via coluna detectada, senão tenta usar qualquer campo "dia/data"
        dt = getattr(t, DATE_COL.key) if DATE_COL is not None else getattr(t, "dia", None) or getattr(t, "data", None)
        dia = dt.strftime("%Y-%m-%d") if dt else "sem-data"

        if dia not in dias_map:
            dias_map[dia] = {"dia": dia, "entradas": 0.0, "saidas": 0.0}

        if getattr(t, "tipo", "") == "recebido":
            dias_map[dia]["entradas"] += float(getattr(t, "valor", 0) or 0)
        else:
            dias_map[dia]["saidas"] += float(getattr(t, "valor", 0) or 0)

    return {
        "dias": list(dias_map.values()),
        "history": transactions,
    }
