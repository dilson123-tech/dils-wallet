from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import secrets
from typing import Any

from app.models.idempotency import IdempotencyKey


ASAAS_PAYMENT_EXTERNAL_REFERENCE_PREFIX = "agpay_"
ASAAS_PAYMENT_CORRELATION_KEY_PREFIX = "asaas-payment-correlation:"
ASAAS_PAYMENT_CORRELATION_CONTRACT = (
    "asaas_payment_user_correlation_v1"
)
# Mesmo valor de ASAAS_CORRELATED_PIX_PAYMENT_PREPARATION_CONTRACT
# (app/services/asaas_correlated_pix_payment_service.py). Duplicado aqui
# para evitar import circular (o serviço importa este módulo).
_ASAAS_PIX_PAYMENT_PREPARATION_CONTRACT = (
    "asaas_correlated_pix_payment_preparation_v1"
)

_EXTERNAL_REFERENCE_PATTERN = re.compile(
    rf"^{ASAAS_PAYMENT_EXTERNAL_REFERENCE_PREFIX}[a-f0-9]{{32}}$"
)


@dataclass(frozen=True)
class AsaasPaymentUserCorrelation:
    user_id: int
    correlation_key: str
    provider: str = "asaas"
    environment: str = "sandbox"
    raw_external_reference_stored: bool = False
    # Valor da cobrança preparada (P0.3), quando a correlação foi
    # registrada por prepare_asaas_correlated_pix_payment com o valor
    # persistido. None = indisponível (ex.: registro legado) e o crédito
    # sandbox deve falhar fechado.
    prepared_amount: Decimal | None = field(default=None, repr=False)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "environment": self.environment,
            "user_id_present": True,
            "correlation_key_present": bool(self.correlation_key),
            "external_reference_present": True,
            "raw_external_reference_stored": (
                self.raw_external_reference_stored
            ),
            "correlation_status": "resolved",
        }


def generate_asaas_payment_external_reference() -> str:
    return (
        f"{ASAAS_PAYMENT_EXTERNAL_REFERENCE_PREFIX}"
        f"{secrets.token_hex(16)}"
    )


def validate_asaas_payment_external_reference(
    external_reference: str,
) -> str:
    normalized = str(external_reference or "").strip()

    if not _EXTERNAL_REFERENCE_PATTERN.fullmatch(normalized):
        raise ValueError(
            "external_reference Asaas deve ser uma referência opaca "
            "gerada pela Aurea Gold."
        )

    return normalized


def asaas_payment_correlation_key(
    external_reference: str,
) -> str:
    normalized = validate_asaas_payment_external_reference(
        external_reference
    )
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{ASAAS_PAYMENT_CORRELATION_KEY_PREFIX}{digest}"


def _normalize_user_id(user_id: int) -> int:
    if isinstance(user_id, bool):
        raise ValueError("user_id inválido para correlação Asaas.")

    try:
        normalized = int(user_id)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "user_id inválido para correlação Asaas."
        ) from exc

    if normalized <= 0:
        raise ValueError("user_id inválido para correlação Asaas.")

    return normalized


def build_asaas_payment_user_correlation_record(
    *,
    user_id: int,
    external_reference: str,
) -> IdempotencyKey:
    normalized_user_id = _normalize_user_id(user_id)
    correlation_key = asaas_payment_correlation_key(
        external_reference
    )

    request_hash = hashlib.sha256(
        f"{correlation_key}|{normalized_user_id}".encode("utf-8")
    ).hexdigest()

    stored_contract = {
        "contract": ASAAS_PAYMENT_CORRELATION_CONTRACT,
        "provider": "asaas",
        "environment": "sandbox",
        "user_id": normalized_user_id,
        "correlation_status": "registered",
        "external_reference_present": True,
        "raw_external_reference_stored": False,
        "can_credit_balance": False,
        "real_money_enabled": False,
    }

    return IdempotencyKey(
        key=correlation_key,
        request_hash=request_hash,
        status_code=201,
        response_json=json.dumps(
            stored_contract,
            ensure_ascii=False,
            sort_keys=True,
        ),
    )


def _stored_prepared_amount(
    stored_contract: dict,
    *,
    request_hash: str | None,
) -> Decimal | None:
    if (
        stored_contract.get("preparation_contract")
        != _ASAAS_PIX_PAYMENT_PREPARATION_CONTRACT
    ):
        return None

    if (
        not request_hash
        or stored_contract.get("prepared_request_hash") != request_hash
        or stored_contract.get("billing_type") != "PIX"
        or stored_contract.get("prepared_currency") != "BRL"
        or stored_contract.get("real_money_enabled") is not False
    ):
        return None

    raw_amount = stored_contract.get("prepared_amount")
    if not isinstance(raw_amount, str):
        return None

    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, TypeError, ValueError):
        return None

    if (
        not amount.is_finite()
        or amount <= Decimal("0.00")
        or amount != amount.quantize(Decimal("0.01"))
    ):
        return None

    return amount.quantize(Decimal("0.01"))


def resolve_asaas_payment_user_correlation(
    db,
    *,
    external_reference: str,
) -> AsaasPaymentUserCorrelation | None:
    correlation_key = asaas_payment_correlation_key(
        external_reference
    )
    record = (
        db.query(IdempotencyKey)
        .filter_by(key=correlation_key)
        .first()
    )

    if not record or not getattr(record, "response_json", None):
        return None

    try:
        stored_contract = json.loads(record.response_json)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    if (
        stored_contract.get("contract")
        != ASAAS_PAYMENT_CORRELATION_CONTRACT
    ):
        return None

    try:
        user_id = _normalize_user_id(
            stored_contract.get("user_id")
        )
    except ValueError:
        return None

    return AsaasPaymentUserCorrelation(
        user_id=user_id,
        correlation_key=correlation_key,
        prepared_amount=_stored_prepared_amount(
            stored_contract,
            request_hash=getattr(record, "request_hash", None),
        ),
    )


def resolve_asaas_payment_user_correlation_from_payment(
    db,
    *,
    payment_payload: dict,
) -> AsaasPaymentUserCorrelation | None:
    if not isinstance(payment_payload, dict):
        return None

    external_reference = (
        payment_payload.get("externalReference")
        or payment_payload.get("external_reference")
    )

    if external_reference is None:
        return None

    try:
        return resolve_asaas_payment_user_correlation(
            db,
            external_reference=str(external_reference),
        )
    except ValueError:
        return None
