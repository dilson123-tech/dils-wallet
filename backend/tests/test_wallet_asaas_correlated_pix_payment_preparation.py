import json
import os
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

from app.models.idempotency import IdempotencyKey
from app.partner.asaas_client import AsaasSandboxClient
from app.partner.asaas_config import (
    ASAAS_SANDBOX_BASE_URL,
    AsaasSandboxConfig,
)
from app.services.asaas_correlated_pix_payment_service import (
    AsaasCorrelatedPixPaymentConflictError,
    AsaasCorrelatedPixPaymentStorageError,
    prepare_asaas_correlated_pix_payment,
)


TEST_CONFIG = AsaasSandboxConfig(
    env="sandbox",
    base_url=ASAAS_SANDBOX_BASE_URL,
    api_key="sandbox-api-key-for-test-only",
    webhook_token="sandbox-webhook-token-for-test-only",
    real_money_enabled=False,
    wallet_mode="partner",
    wallet_partner_provider="asaas",
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
    def __init__(self, *, fail_commit=False):
        self.records = {}
        self.pending = None
        self.inserted_keys = []
        self.committed = False
        self.rolled_back = False
        self.fail_commit = fail_commit

    def add(self, record):
        self.pending = record

    def flush(self):
        if self.pending.key in self.records:
            raise IntegrityError(
                "duplicate",
                {},
                Exception("duplicate"),
            )

        key = self.pending.key
        self.records[key] = self.pending
        self.inserted_keys.append(key)
        self.pending = None

    def commit(self):
        if self.fail_commit:
            raise SQLAlchemyError(
                "database unavailable with secret value"
            )

        self.committed = True
        self.inserted_keys.clear()

    def rollback(self):
        self.rolled_back = True
        self.pending = None

        for key in self.inserted_keys:
            self.records.pop(key, None)

        self.inserted_keys.clear()

    def query(self, model):
        assert model is IdempotencyKey
        return FakeQuery(self)


def _client() -> AsaasSandboxClient:
    return AsaasSandboxClient(config=TEST_CONFIG)


def _external_reference(character: str) -> str:
    return f"agpay_{character * 32}"


def test_prepares_correlated_pix_payment_and_commits_before_http():
    db = FakeDb()
    external_reference = _external_reference("a")

    result = prepare_asaas_correlated_pix_payment(
        db,
        client=_client(),
        user_id=321,
        customer_id="cus_correlated_test",
        value=Decimal("49.90"),
        due_date="2026-07-20",
        description="Cobrança correlacionada Sandbox",
        external_reference=external_reference,
    )

    request = result.prepared_request
    stored_record = db.records[result.correlation_key]
    stored_contract = json.loads(
        stored_record.response_json
    )
    safe_summary = result.safe_summary()
    rendered_summary = json.dumps(
        safe_summary,
        ensure_ascii=False,
        default=str,
    )

    assert db.committed is True
    assert result.correlation_replayed is False
    assert request.method == "POST"
    assert request.operation == "create_pix_payment"
    assert request.json["externalReference"] == (
        external_reference
    )
    assert request.json["value"] == 49.9
    assert request.http_call_executed is False
    assert request.real_money is False

    assert stored_contract["user_id"] == 321
    assert (
        stored_contract["preparation_contract"]
        == "asaas_correlated_pix_payment_preparation_v1"
    )
    assert stored_contract["http_call_executed"] is False
    assert stored_contract["can_send_http"] is False
    assert stored_contract["real_money_enabled"] is False

    assert external_reference not in stored_record.response_json
    assert "cus_correlated_test" not in stored_record.response_json
    assert external_reference not in rendered_summary
    assert "cus_correlated_test" not in rendered_summary
    assert external_reference not in repr(result)
    assert "sandbox-api-key-for-test-only" not in rendered_summary
    assert "sandbox-webhook-token-for-test-only" not in rendered_summary


def test_generated_reference_is_sent_and_not_stored_raw():
    db = FakeDb()

    result = prepare_asaas_correlated_pix_payment(
        db,
        client=_client(),
        user_id=654,
        customer_id="cus_generated_reference",
        value=Decimal("10.00"),
        due_date="2026-07-21",
        description="Referência gerada",
    )

    external_reference = result.external_reference
    stored_record = db.records[result.correlation_key]

    assert external_reference.startswith("agpay_")
    assert len(external_reference) == len("agpay_") + 32
    assert (
        result.prepared_request.json[
            "externalReference"
        ]
        == external_reference
    )
    assert external_reference not in stored_record.response_json
    assert external_reference not in repr(result)


def test_same_preparation_is_idempotent():
    db = FakeDb()
    external_reference = _external_reference("b")
    kwargs = {
        "client": _client(),
        "user_id": 321,
        "customer_id": "cus_idempotent",
        "value": Decimal("25.00"),
        "due_date": "2026-07-22",
        "description": "Preparação idempotente",
        "external_reference": external_reference,
    }

    first = prepare_asaas_correlated_pix_payment(
        db,
        **kwargs,
    )
    second = prepare_asaas_correlated_pix_payment(
        db,
        **kwargs,
    )

    assert first.correlation_replayed is False
    assert second.correlation_replayed is True
    assert first.correlation_key == second.correlation_key
    assert len(db.records) == 1
    assert second.prepared_request.http_call_executed is False


def test_reused_reference_with_different_payment_conflicts():
    db = FakeDb()
    external_reference = _external_reference("c")

    prepare_asaas_correlated_pix_payment(
        db,
        client=_client(),
        user_id=321,
        customer_id="cus_conflict",
        value=Decimal("30.00"),
        due_date="2026-07-23",
        description="Primeira preparação",
        external_reference=external_reference,
    )

    with pytest.raises(
        AsaasCorrelatedPixPaymentConflictError
    ):
        prepare_asaas_correlated_pix_payment(
            db,
            client=_client(),
            user_id=321,
            customer_id="cus_conflict",
            value=Decimal("31.00"),
            due_date="2026-07-23",
            description="Preparação alterada",
            external_reference=external_reference,
        )

    assert len(db.records) == 1


@pytest.mark.parametrize(
    "user_id,value,external_reference",
    [
        (0, Decimal("10.00"), _external_reference("d")),
        (321, Decimal("0.00"), _external_reference("e")),
        (321, Decimal("10.00"), "user-321-payment"),
    ],
)
def test_invalid_preparation_does_not_register_correlation(
    user_id,
    value,
    external_reference,
):
    db = FakeDb()

    with pytest.raises(ValueError):
        prepare_asaas_correlated_pix_payment(
            db,
            client=_client(),
            user_id=user_id,
            customer_id="cus_invalid",
            value=value,
            due_date="2026-07-24",
            description="Preparação inválida",
            external_reference=external_reference,
        )

    assert db.records == {}
    assert db.committed is False


def test_storage_failure_rolls_back_without_exposing_error():
    db = FakeDb(fail_commit=True)
    external_reference = _external_reference("f")

    with pytest.raises(
        AsaasCorrelatedPixPaymentStorageError
    ) as exc:
        prepare_asaas_correlated_pix_payment(
            db,
            client=_client(),
            user_id=321,
            customer_id="cus_storage_failure",
            value=Decimal("15.00"),
            due_date="2026-07-25",
            description="Falha controlada",
            external_reference=external_reference,
        )

    assert db.rolled_back is True
    assert db.records == {}
    assert external_reference not in str(exc.value)
    assert "secret value" not in str(exc.value)
