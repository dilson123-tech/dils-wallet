from sqlalchemy.orm import Session
from fastapi import HTTPException
from .. import models

ALLOWED_TYPES = {"deposito", "saque", "transferencia"}

def create_transaction(payload, db: Session, current_user):
    t = (payload.tipo or "").strip().lower()

    if t not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"tipo inválido. Use: {sorted(ALLOWED_TYPES)}"
        )

    kind = "credit" if t == "deposito" else "debit"

    try:
        value = float(payload.valor)
    except Exception:
        raise HTTPException(status_code=400, detail="valor inválido")

    if value <= 0:
        raise HTTPException(status_code=400, detail="valor deve ser > 0")

    # Verificação de saldo para saque/transferência
    if t in ("saque", "transferencia"):
        from sqlalchemy import func, case

        saldo_q = db.query(
            func.coalesce(
                func.sum(
                    case(
                        (models.Transaction.kind == "credit", models.Transaction.amount),
                        (models.Transaction.kind == "debit", -models.Transaction.amount),
                        else_=0.0,
                    )
                ),
                0.0,
            )
        ).filter(models.Transaction.user_id == current_user.id)

        saldo_atual = float(saldo_q.scalar() or 0.0)

        if value > saldo_atual:
            raise HTTPException(status_code=400, detail="Saldo insuficiente")

    tx = models.Transaction(
        user_id=current_user.id,
        kind=kind,
        amount=value,
        description=getattr(payload, "referencia", None)
                    or getattr(payload, "descricao", None)
                    or "",
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)

    return tx


def get_summary(db: Session, current_user):
    from sqlalchemy import func, case

    saldo_q = db.query(
        func.coalesce(
            func.sum(
                case(
                    (models.Transaction.kind == "credit", models.Transaction.amount),
                    (models.Transaction.kind == "debit", -models.Transaction.amount),
                    else_=0.0,
                )
            ),
            0.0,
        )
    ).filter(models.Transaction.user_id == current_user.id)

    saldo = float(saldo_q.scalar() or 0.0)

    return {
        "saldo": saldo
    }
