import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.v1.routes import wallet as wallet_routes


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
        self.pending = None
        self.committed = False
        self.rolled_back = False

    def add(self, record):
        self.pending = record

    def flush(self):
        if self.pending.key in self.records:
            raise IntegrityError("duplicate", {}, Exception("duplicate"))
        self.records[self.pending.key] = self.pending
        self.pending = None

    def rollback(self):
        self.rolled_back = True

    def commit(self):
        self.committed = True

    def query(self, _model):
        return FakeQuery(self)


def _valid_payload():
    return {
        "id": "evt_test_unique_001",
        "event": "PAYMENT_RECEIVED",
        "payment": {
            "id": "pay_real_sandbox_must_not_leak",
            "status": "RECEIVED",
            "billingType": "PIX",
        },
    }


@pytest.fixture(autouse=True)
def asaas_receiver_setup(monkeypatch):
    monkeypatch.setattr(
        wallet_routes,
        "load_asaas_sandbox_config",
        lambda: SimpleNamespace(webhook_token="secret-token"),
    )


def test_asaas_sandbox_webhook_accepts_payment_received_without_exposing_sensitive_values():
    db = FakeDb()

    response = wallet_routes.handle_asaas_sandbox_webhook_receiver(
        payload=_valid_payload(),
        db=db,
        asaas_access_token="secret-token",
    )

    encoded = json.dumps(response, ensure_ascii=False, default=str)

    assert response["ok"] is True
    assert response["event"]["event_type"] == "PAYMENT_RECEIVED"
    assert response["event"]["accepted"] is True
    assert response["payment"]["payment_id_present"] is True
    assert response["can_credit_balance"] is False
    assert response["can_generate_real_receipt"] is False
    assert response["can_mark_real_paid"] is False
    assert "secret-token" not in encoded
    assert "pay_real_sandbox_must_not_leak" not in encoded
    assert "evt_test_unique_001" not in encoded
    assert db.committed is True


def test_asaas_sandbox_webhook_rejects_invalid_token():
    db = FakeDb()

    with pytest.raises(HTTPException) as exc:
        wallet_routes.handle_asaas_sandbox_webhook_receiver(
            payload=_valid_payload(),
            db=db,
            asaas_access_token="wrong-token",
        )

    assert exc.value.status_code == 403


def test_asaas_sandbox_webhook_is_idempotent_for_same_event():
    db = FakeDb()

    first = wallet_routes.handle_asaas_sandbox_webhook_receiver(
        payload=_valid_payload(),
        db=db,
        asaas_access_token="secret-token",
    )
    second = wallet_routes.handle_asaas_sandbox_webhook_receiver(
        payload=_valid_payload(),
        db=db,
        asaas_access_token="secret-token",
    )

    assert first["duplicated"] is False
    assert second["duplicated"] is True
    assert second["idempotency"]["replayed"] is True
    assert db.rolled_back is True


def test_asaas_sandbox_webhook_ignores_non_payment_received_events_safely():
    db = FakeDb()
    payload = {
        "id": "evt_test_unique_002",
        "event": "PAYMENT_CREATED",
        "payment": {
            "id": "pay_created_must_not_leak",
            "status": "PENDING",
            "billingType": "PIX",
        },
    }

    response = wallet_routes.handle_asaas_sandbox_webhook_receiver(
        payload=payload,
        db=db,
        asaas_access_token="secret-token",
    )

    encoded = json.dumps(response, ensure_ascii=False, default=str)

    assert response["ok"] is True
    assert response["event"]["accepted"] is False
    assert response["event"]["ignored"] is True
    assert response["can_credit_balance"] is False
    assert "pay_created_must_not_leak" not in encoded
