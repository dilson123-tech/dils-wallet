from sqlalchemy.exc import IntegrityError
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.pix_transaction import PixTransaction
from app.models.pix_ledger import PixLedger


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get_user_balance(db: Session, user_id: int) -> Decimal:
    result = (
        db.query(
            func.coalesce(
                func.sum(
                    case(
                        (PixLedger.kind == "credit", PixLedger.amount),
                        else_=-PixLedger.amount,
                    )
                ),
                0,
            )
        )
        .filter(PixLedger.user_id == user_id)
        .scalar()
    )

    return Decimal(result or 0)


def send_pix(
    db: Session,
    user_id: int,
    valor: Decimal,
    chave_pix: str,
    descricao: str = "PIX",
    idempotency_key: str | None = None,
):
    valor = _round_money(Decimal(valor))
    # -----------------------------
    # Idempotency (atomic insert first)
    # -----------------------------
    if idempotency_key:
        from app.models.idempotency import IdempotencyKey
        import json

        try:
            record = IdempotencyKey(key=idempotency_key)
            db.add(record)
            db.flush()
        except IntegrityError:
            db.rollback()
            existing = db.query(IdempotencyKey).filter_by(key=idempotency_key).first()
            if existing and existing.response_json:
                return json.loads(existing.response_json)
            raise

    # -----------------------------


    taxa_percentual = Decimal("0.0000")
    taxa_valor = Decimal("0.00")
    valor_liquido = valor

    from sqlalchemy import select
    from app.models.pix_ledger import PixLedger

    db.execute(
        select(PixLedger)
        .where(PixLedger.user_id == user_id)
        .with_for_update()
    )

    saldo_atual = _get_user_balance(db, user_id)

    if saldo_atual < valor:
        raise ValueError("Saldo insuficiente")

    tx = PixTransaction(
        user_id=user_id,
        tipo="saida",
        valor=valor,
        descricao=descricao,
        taxa_percentual=taxa_percentual,
        taxa_valor=taxa_valor,
        valor_liquido=valor_liquido,
    )

    db.add(tx)
    db.flush()

    ledger_entry = PixLedger(
        user_id=user_id,
        kind="debit",
        amount=valor,
        ref_tx_id=tx.id,
        description=descricao,
    )

    db.add(ledger_entry)

    if idempotency_key:
        from app.models.idempotency import IdempotencyKey
        import json
        record = db.query(IdempotencyKey).filter_by(key=idempotency_key).first()
        if record:
            record.status_code = 200
            record.response_json = json.dumps({
                "id": tx.id,
                "valor": str(tx.valor),
                "taxa_percentual": str(tx.taxa_percentual),
                "taxa_valor": str(tx.taxa_valor),
                "valor_liquido": str(tx.valor_liquido),
                "status": "success"
            })

    db.commit()
    db.refresh(tx)

    return tx
