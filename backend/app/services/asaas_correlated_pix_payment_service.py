from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.idempotency import IdempotencyKey
from app.partner.asaas_client import (
    AsaasPreparedRequest,
    AsaasSandboxClient,
)
from app.partner.asaas_payment_correlation import (
    build_asaas_payment_user_correlation_record,
    generate_asaas_payment_external_reference,
    validate_asaas_payment_external_reference,
)


ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT = (
    "asaas_correlated_pix_payment_preparation_v1"
)


class AsaasCorrelatedPixPaymentConflictError(RuntimeError):
    pass


class AsaasCorrelatedPixPaymentStorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class AsaasCorrelatedPixPaymentPreparation:
    user_id: int = field(repr=False)
    external_reference: str = field(repr=False)
    correlation_key: str = field(repr=False)
    prepared_request: AsaasPreparedRequest = field(repr=False)
    correlation_replayed: bool = False
    sandbox_only: bool = True
    real_money: bool = False
    http_call_executed: bool = False
    can_send_http: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "operation": (
                "prepare_asaas_correlated_pix_payment"
            ),
            "provider": "asaas",
            "environment": "sandbox",
            "user_id_present": True,
            "external_reference_present": True,
            "correlation_key_present": True,
            "raw_external_reference_stored": False,
            "correlation_replayed": (
                self.correlation_replayed
            ),
            "prepared_request": {
                "method": self.prepared_request.method,
                "operation": (
                    self.prepared_request.operation
                ),
                "external_reference_present": True,
                "headers_configured": (
                    self.prepared_request.headers_configured
                ),
                "real_money": (
                    self.prepared_request.real_money
                ),
                "http_call_executed": (
                    self.prepared_request.http_call_executed
                ),
            },
            "sandbox_only": self.sandbox_only,
            "real_money": self.real_money,
            "http_call_executed": (
                self.http_call_executed
            ),
            "can_send_http": self.can_send_http,
        }


def _required_text(value, *, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} é obrigatório.")
    return normalized


def _positive_amount(value) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ValueError(
            "value deve ser maior que zero."
        )

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            "value deve ser um valor monetário válido."
        ) from exc

    if not amount.is_finite() or amount <= Decimal("0.00"):
        raise ValueError(
            "value deve ser maior que zero."
        )

    return amount


def _preparation_hash(
    *,
    user_id: int,
    correlation_key: str,
    customer_id: str,
    value: Decimal,
    due_date: str,
    description: str,
) -> str:
    contract = {
        "contract": (
            ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT
        ),
        "user_id": user_id,
        "correlation_key": correlation_key,
        "customer_id": customer_id,
        "value": format(value, "f"),
        "due_date": due_date,
        "description": description,
    }
    encoded = json.dumps(
        contract,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _stored_preparation_contract(
    *,
    correlation_record: IdempotencyKey,
    preparation_hash: str,
) -> str:
    stored_contract = json.loads(
        correlation_record.response_json or "{}"
    )
    stored_contract.update(
        {
            "preparation_contract": (
                ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT
            ),
            "prepared_request_hash": preparation_hash,
            "payment_operation": "create_pix_payment",
            "billing_type": "PIX",
            "prepared_request_present": True,
            "external_reference_present": True,
            "raw_external_reference_stored": False,
            "http_call_executed": False,
            "can_send_http": False,
            "real_money_enabled": False,
        }
    )
    return json.dumps(
        stored_contract,
        ensure_ascii=False,
        sort_keys=True,
    )


def _existing_preparation_matches(
    existing: IdempotencyKey,
    *,
    preparation_hash: str,
) -> bool:
    if (
        getattr(existing, "request_hash", None)
        != preparation_hash
    ):
        return False

    try:
        stored_contract = json.loads(
            existing.response_json or "{}"
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        return False

    return (
        stored_contract.get("preparation_contract")
        == ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT
        and stored_contract.get("prepared_request_hash")
        == preparation_hash
        and stored_contract.get("http_call_executed")
        is False
        and stored_contract.get("real_money_enabled")
        is False
    )


def prepare_asaas_correlated_pix_payment(
    db,
    *,
    client: AsaasSandboxClient,
    user_id: int,
    customer_id: str,
    value: Decimal,
    due_date: str,
    description: str,
    external_reference: str | None = None,
) -> AsaasCorrelatedPixPaymentPreparation:
    normalized_customer_id = _required_text(
        customer_id,
        field_name="customer_id",
    )
    normalized_due_date = _required_text(
        due_date,
        field_name="due_date",
    )
    normalized_description = _required_text(
        description,
        field_name="description",
    )
    normalized_value = _positive_amount(value)

    generated_reference = (
        external_reference
        if external_reference is not None
        else generate_asaas_payment_external_reference()
    )
    normalized_external_reference = (
        validate_asaas_payment_external_reference(
            generated_reference
        )
    )

    correlation_record = (
        build_asaas_payment_user_correlation_record(
            user_id=user_id,
            external_reference=(
                normalized_external_reference
            ),
        )
    )
    stored_correlation = json.loads(
        correlation_record.response_json or "{}"
    )
    normalized_user_id = int(
        stored_correlation["user_id"]
    )

    prepared_request = client.prepare_create_pix_payment(
        customer_id=normalized_customer_id,
        value=normalized_value,
        due_date=normalized_due_date,
        description=normalized_description,
        external_reference=(
            normalized_external_reference
        ),
    )

    preparation_hash = _preparation_hash(
        user_id=normalized_user_id,
        correlation_key=correlation_record.key,
        customer_id=normalized_customer_id,
        value=normalized_value,
        due_date=normalized_due_date,
        description=normalized_description,
    )

    correlation_record.request_hash = preparation_hash
    correlation_record.response_json = (
        _stored_preparation_contract(
            correlation_record=correlation_record,
            preparation_hash=preparation_hash,
        )
    )

    replayed = False

    try:
        db.add(correlation_record)
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(IdempotencyKey)
            .filter_by(key=correlation_record.key)
            .first()
        )

        if not existing or not _existing_preparation_matches(
            existing,
            preparation_hash=preparation_hash,
        ):
            raise AsaasCorrelatedPixPaymentConflictError(
                "Referência de correlação já utilizada "
                "por outra preparação."
            ) from None

        replayed = True
    except SQLAlchemyError:
        db.rollback()
        raise AsaasCorrelatedPixPaymentStorageError(
            "Não foi possível registrar a correlação "
            "da cobrança Asaas Sandbox."
        ) from None

    return AsaasCorrelatedPixPaymentPreparation(
        user_id=normalized_user_id,
        external_reference=(
            normalized_external_reference
        ),
        correlation_key=correlation_record.key,
        prepared_request=prepared_request,
        correlation_replayed=replayed,
    )
