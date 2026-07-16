import json
import os
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

from app.api.v1.routes import wallet as wallet_routes
from app.partner.asaas_config import (
    ASAAS_SANDBOX_BASE_URL,
    AsaasConfigError,
    AsaasSandboxConfig,
)
from app.services import (
    asaas_correlated_pix_payment_service as correlated_service,
)


TEST_CONFIG = AsaasSandboxConfig(
    env="sandbox",
    base_url=ASAAS_SANDBOX_BASE_URL,
    api_key="endpoint-api-key-must-not-leak",
    webhook_token="endpoint-webhook-token-must-not-leak",
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
        self.inserted_key = None
        self.fail_commit = fail_commit
        self.commit_count = 0
        self.rollback_count = 0

    def add(self, row):
        self.pending = row

    def flush(self):
        if self.pending.key in self.records:
            raise IntegrityError(
                "insert",
                {},
                Exception("duplicate"),
            )

        self.records[self.pending.key] = self.pending
        self.inserted_key = self.pending.key

    def commit(self):
        if self.fail_commit:
            raise SQLAlchemyError("simulated storage failure")

        self.commit_count += 1
        self.pending = None
        self.inserted_key = None

    def rollback(self):
        self.rollback_count += 1

        if self.inserted_key is not None:
            self.records.pop(self.inserted_key, None)

        self.pending = None
        self.inserted_key = None

    def query(self, model):
        return FakeQuery(self)


def _configure_sandbox(monkeypatch):
    monkeypatch.setattr(
        wallet_routes,
        "load_asaas_sandbox_config",
        lambda: TEST_CONFIG,
    )


def _payload(
    *,
    amount=Decimal("49.90"),
    customer_id="cus_endpoint_must_not_leak",
):
    return (
        wallet_routes
        .WalletAsaasCorrelatedPixPaymentPreparationIn(
            customer_id=customer_id,
            amount=amount,
            due_date="2026-07-30",
            description="Cobrança correlacionada via endpoint",
        )
    )


def test_endpoint_prepares_correlated_pix_without_http_or_sensitive_output(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)

    external_reference = f"agpay_{'a' * 32}"
    monkeypatch.setattr(
        correlated_service,
        "generate_asaas_payment_external_reference",
        lambda: external_reference,
    )

    db = FakeDb()
    user = SimpleNamespace(id=321)

    response = (
        wallet_routes
        .prepare_wallet_asaas_correlated_pix_payment(
            payload=_payload(),
            current_user=user,
            db=db,
        )
    )

    encoded = json.dumps(
        response,
        ensure_ascii=False,
        default=str,
    )

    assert response["ok"] is True
    assert response["operation"] == (
        "prepare_asaas_correlated_pix_payment"
    )
    assert response["preparation"]["provider"] == "asaas"
    assert response["preparation"]["environment"] == "sandbox"
    assert response["preparation"]["external_reference_present"] is True
    assert response["preparation"]["correlation_key_present"] is True
    assert response["preparation"]["http_call_executed"] is False
    assert response["preparation"]["can_send_http"] is False
    assert response["can_send_http"] is False
    assert response["can_create_charge"] is False
    assert response["can_credit_balance"] is False
    assert response["wallet"]["real_money_enabled"] is False
    assert db.commit_count == 1
    assert len(db.records) == 1

    assert external_reference not in encoded
    assert "cus_endpoint_must_not_leak" not in encoded
    assert "endpoint-api-key-must-not-leak" not in encoded
    assert "endpoint-webhook-token-must-not-leak" not in encoded
    assert "correlation_key" not in response
    assert "customer_id" not in response
    assert "external_reference" not in response


def test_endpoint_replays_identical_preparation_idempotently(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)

    external_reference = f"agpay_{'b' * 32}"
    monkeypatch.setattr(
        correlated_service,
        "generate_asaas_payment_external_reference",
        lambda: external_reference,
    )

    db = FakeDb()
    user = SimpleNamespace(id=321)
    payload = _payload()

    first = (
        wallet_routes
        .prepare_wallet_asaas_correlated_pix_payment(
            payload=payload,
            current_user=user,
            db=db,
        )
    )
    replay = (
        wallet_routes
        .prepare_wallet_asaas_correlated_pix_payment(
            payload=payload,
            current_user=user,
            db=db,
        )
    )

    assert first["preparation"]["correlation_replayed"] is False
    assert replay["preparation"]["correlation_replayed"] is True
    assert len(db.records) == 1
    assert db.commit_count == 1
    assert db.rollback_count == 1


def test_endpoint_rejects_reference_reuse_with_changed_data(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)

    external_reference = f"agpay_{'c' * 32}"
    monkeypatch.setattr(
        correlated_service,
        "generate_asaas_payment_external_reference",
        lambda: external_reference,
    )

    db = FakeDb()
    user = SimpleNamespace(id=321)

    wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
        payload=_payload(amount=Decimal("10.00")),
        current_user=user,
        db=db,
    )

    with pytest.raises(HTTPException) as captured:
        wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
            payload=_payload(amount=Decimal("11.00")),
            current_user=user,
            db=db,
        )

    assert captured.value.status_code == 409
    assert "agpay_" not in str(captured.value.detail)
    assert "cus_endpoint_must_not_leak" not in str(
        captured.value.detail
    )


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0.00"),
        Decimal("-1.00"),
    ],
)
def test_endpoint_rejects_non_positive_amount(
    monkeypatch,
    amount,
):
    _configure_sandbox(monkeypatch)

    with pytest.raises(HTTPException) as captured:
        wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
            payload=_payload(amount=amount),
            current_user=SimpleNamespace(id=321),
            db=FakeDb(),
        )

    assert captured.value.status_code == 422
    assert "maior que zero" in str(captured.value.detail)


def test_endpoint_maps_storage_failure_to_sanitized_503(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)

    external_reference = f"agpay_{'d' * 32}"
    monkeypatch.setattr(
        correlated_service,
        "generate_asaas_payment_external_reference",
        lambda: external_reference,
    )

    with pytest.raises(HTTPException) as captured:
        wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
            payload=_payload(),
            current_user=SimpleNamespace(id=321),
            db=FakeDb(fail_commit=True),
        )

    assert captured.value.status_code == 503
    assert external_reference not in str(captured.value.detail)
    assert "endpoint-api-key-must-not-leak" not in str(
        captured.value.detail
    )


def test_endpoint_rejects_invalid_authenticated_user(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)

    with pytest.raises(HTTPException) as captured:
        wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
            payload=_payload(),
            current_user=SimpleNamespace(id=None),
            db=FakeDb(),
        )

    assert captured.value.status_code == 403


def test_endpoint_maps_invalid_sandbox_config_to_sanitized_503(
    monkeypatch,
):
    monkeypatch.setattr(
        wallet_routes,
        "load_asaas_sandbox_config",
        lambda: (_ for _ in ()).throw(
            AsaasConfigError("sensitive config detail")
        ),
    )

    with pytest.raises(HTTPException) as captured:
        wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
            payload=_payload(),
            current_user=SimpleNamespace(id=321),
            db=FakeDb(),
        )

    assert captured.value.status_code == 503
    assert "sensitive config detail" not in str(
        captured.value.detail
    )
