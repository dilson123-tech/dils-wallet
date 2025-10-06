from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.deps import get_db
from backend.app.models.pix_transaction import PixTransaction

router = APIRouter(prefix="/api/v1/pix", tags=["PIX"])

@router.get("/summary")
def get_pix_summary(db: Session = Depends(get_db)):
    """
    Retorna resumo por conta:
    - total enviado
    - total recebido
    - saldo líquido (recebido - enviado)
    """
    # total enviado por conta (from)
    sent_subq = (
        db.query(
            PixTransaction.from_account_id.label("account_id"),
            func.sum(PixTransaction.amount).label("total_sent"),
        )
        .group_by(PixTransaction.from_account_id)
        .subquery()
    )

    # total recebido por conta (to)
    recv_subq = (
        db.query(
            PixTransaction.to_account_id.label("account_id"),
            func.sum(PixTransaction.amount).label("total_received"),
        )
        .group_by(PixTransaction.to_account_id)
        .subquery()
    )

    # conjunto de contas que aparecem em from ou to
    accounts_subq = (
        db.query(PixTransaction.from_account_id.label("account_id"))
        .union(db.query(PixTransaction.to_account_id.label("account_id")))
        .subquery()
    )

    rows = (
        db.query(
            accounts_subq.c.account_id,
            func.coalesce(recv_subq.c.total_received, 0.0).label("total_received"),
            func.coalesce(sent_subq.c.total_sent, 0.0).label("total_sent"),
            (
                func.coalesce(recv_subq.c.total_received, 0.0)
                - func.coalesce(sent_subq.c.total_sent, 0.0)
            ).label("net_balance"),
        )
        .outerjoin(sent_subq, sent_subq.c.account_id == accounts_subq.c.account_id)
        .outerjoin(recv_subq, recv_subq.c.account_id == accounts_subq.c.account_id)
        .order_by(accounts_subq.c.account_id.asc())
        .all()
    )

    return [
        {
            "account_id": int(r.account_id),
            "total_received": float(r.total_received),
            "total_sent": float(r.total_sent),
            "net_balance": float(r.net_balance),
        }
        for r in rows
    ]
