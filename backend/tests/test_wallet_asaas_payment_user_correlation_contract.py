import json

import pytest

from app.models.idempotency import IdempotencyKey
from app.partner.asaas_payment_correlation import (
    ASAAS_PAYMENT_CORRELATION_KEY_PREFIX,
    ASAAS_PAYMENT_EXTERNAL_REFERENCE_PREFIX,
    asaas_payment_correlation_key,
    build_asaas_payment_user_correlation_record,
    generate_asaas_payment_external_reference,
    resolve_asaas_payment_user_correlation_from_payment,
    validate_asaas_payment_external_reference,
)


class FakeQuery:
    def __init__(self, db):
        self.db = db
        self.key = None

    def filter_by(self, **kwargs):
        self.key = kwargs.get("key")
        return self

    def first(self):
        return self.db.records.get(self.key)


class FakeDb:
    def __init__(self):
        self.records = {}

    def query(self, model):
        assert model is IdempotencyKey
        return FakeQuery(self)


def _opaque_reference(character: str = "a") -> str:
    return (
        f"{ASAAS_PAYMENT_EXTERNAL_REFERENCE_PREFIX}"
        f"{character * 32}"
    )


def test_generated_external_reference_is_opaque_and_valid():
    external_reference = (
        generate_asaas_payment_external_reference()
    )

    assert external_reference.startswith(
        ASAAS_PAYMENT_EXTERNAL_REFERENCE_PREFIX
    )
    assert len(external_reference) == (
        len(ASAAS_PAYMENT_EXTERNAL_REFERENCE_PREFIX) + 32
    )
    assert (
        validate_asaas_payment_external_reference(
            external_reference
        )
        == external_reference
    )


@pytest.mark.parametrize(
    "external_reference",
    [
        "",
        "321",
        "user-321-payment",
        "agpay_short",
        f"{ASAAS_PAYMENT_EXTERNAL_REFERENCE_PREFIX}{'g' * 32}",
    ],
)
def test_external_reference_rejects_non_opaque_values(
    external_reference,
):
    with pytest.raises(ValueError):
        validate_asaas_payment_external_reference(
            external_reference
        )


def test_correlation_record_stores_user_without_raw_reference():
    external_reference = _opaque_reference("b")

    record = build_asaas_payment_user_correlation_record(
        user_id=321,
        external_reference=external_reference,
    )
    stored_contract = json.loads(record.response_json)

    assert record.key.startswith(
        ASAAS_PAYMENT_CORRELATION_KEY_PREFIX
    )
    assert external_reference not in record.key
    assert external_reference not in record.request_hash
    assert external_reference not in record.response_json
    assert stored_contract["user_id"] == 321
    assert (
        stored_contract["raw_external_reference_stored"]
        is False
    )
    assert stored_contract["real_money_enabled"] is False
    assert stored_contract["can_credit_balance"] is False


def test_payment_payload_resolves_only_pre_registered_user():
    db = FakeDb()
    external_reference = _opaque_reference("c")
    record = build_asaas_payment_user_correlation_record(
        user_id=321,
        external_reference=external_reference,
    )
    db.records[record.key] = record

    resolved = (
        resolve_asaas_payment_user_correlation_from_payment(
            db,
            payment_payload={
                "externalReference": external_reference,
                "status": "RECEIVED",
            },
        )
    )

    assert resolved is not None
    assert resolved.user_id == 321
    assert resolved.raw_external_reference_stored is False
    assert resolved.safe_summary() == {
        "provider": "asaas",
        "environment": "sandbox",
        "user_id_present": True,
        "correlation_key_present": True,
        "external_reference_present": True,
        "raw_external_reference_stored": False,
        "correlation_status": "resolved",
    }
    assert external_reference not in repr(
        resolved.safe_summary()
    )


def test_unknown_or_missing_reference_does_not_resolve_user():
    db = FakeDb()

    assert (
        resolve_asaas_payment_user_correlation_from_payment(
            db,
            payment_payload={},
        )
        is None
    )
    assert (
        resolve_asaas_payment_user_correlation_from_payment(
            db,
            payment_payload={
                "externalReference": _opaque_reference("d")
            },
        )
        is None
    )
    assert (
        resolve_asaas_payment_user_correlation_from_payment(
            db,
            payment_payload={
                "externalReference": "user-654-payment"
            },
        )
        is None
    )


def test_same_reference_for_another_user_has_detectable_conflict():
    external_reference = _opaque_reference("e")

    first = build_asaas_payment_user_correlation_record(
        user_id=321,
        external_reference=external_reference,
    )
    second = build_asaas_payment_user_correlation_record(
        user_id=654,
        external_reference=external_reference,
    )

    assert first.key == second.key
    assert first.request_hash != second.request_hash
    assert (
        first.key
        == asaas_payment_correlation_key(
            external_reference
        )
    )
