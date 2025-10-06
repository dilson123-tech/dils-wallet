from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.deps import get_db
from backend.app.models.pix_transaction import PixTransaction

# mesmo prefixo das outras rotas PIX
router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])

@router.get("/summary")
def get_pix_summary(db: Session = Depends(get_db)):
    """
    Retorna resumo agregado do histórico PIX por conta:
    - total enviado
    - total recebido
    - saldo líquido (recebido - enviado)
    """

    # subconsultas de enviados e recebidos
    sent = (
        db.query(
            PixTransaction.from_account_id.label("account_id"),
            func.sum(PixTransaction.amount).label("total_sent")
        )
        .group_by(PixTransaction.from_account_id)
        .subquery()
    )

    received = (
        db.query(
            PixTransaction.to_account_id.label("account_id"),
            func.sum(PixTransaction.amount).label("total_received")
        )
        .group_by(PixTransaction.to_account_id)
        .subquery()
    )

    # conjunto de contas (full coverage): union de from e to
    accounts_subq = (
        db.query(PixTransaction.from_account_id.label("account_id"))
        .union(db.query(PixTransaction.to_account_id.label("account_id")))
        .subquery()
    )

    # junta com sent/received
    rows = (
        db.query(
            accounts_subq.c.account_id.label("account_id"),
            func.coalesce(received.c.total_received, 0.0).label("total_received"),
            func.coalesce(sent.c.total_sent, 0.0).label("total_sent"),
            (func.coalesce(received.c.total_received, 0.0) - func.coalesce(sent.c.total_sent, 0.0)).label("net_balance"),
        )
        .outerjoin(sent, sent.c.account_id == accounts_subq.c.account_id)
        .outerjoin(received, received.c.account_id == accounts_subq.c.account_id)
        .order_by(accounts_subq.c.account_id.asc())
        .all()
    )

    return [
        {
            "account_id": r.account_id,
            "total_received": float(r.total_received),
            "total_sent": float(r.total_sent),
            "net_balance": float(r.net_balance),
        }
        for r in rows
    ]
