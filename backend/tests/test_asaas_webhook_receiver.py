import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.v1.routes import wallet as wallet_routes


class FakeQuery:
    def __init__(self, db):
        self.db = db
        self.key = None
        self.row_limit = None

    def filter_by(self, **kwargs):
        self.key = kwargs.get("key")
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self.row_limit = int(value)
        return self

    def first(self):
        return self.db.records.get(self.key)

    def all(self):
        rows = list(self.db.records.values())
        rows = [row for row in rows if str(row.key).startswith("asaas-sandbox-webhook:")]
        rows.sort(key=lambda row: str(getattr(row, "created_at", "") or ""), reverse=True)
        if self.row_limit is not None:
            rows = rows[: self.row_limit]
        return rows


class FakeDb:
    def __init__(self, *, fail_commit=False):
        self.records = {}
        self.pending = None
        self.committed = False
        self.rolled_back = False
        self.fail_commit = fail_commit
        self.transaction_inserted_keys = []

    def add(self, record):
        self.pending = record

    def flush(self):
        if self.pending.key in self.records:
            raise IntegrityError("duplicate", {}, Exception("duplicate"))
        inserted_key = self.pending.key
        self.records[inserted_key] = self.pending
        self.transaction_inserted_keys.append(inserted_key)
        self.pending = None

    def rollback(self):
        self.rolled_back = True
        self.pending = None
        for key in self.transaction_inserted_keys:
            self.records.pop(key, None)
        self.transaction_inserted_keys.clear()

    def commit(self):
        if self.fail_commit:
            raise SQLAlchemyError(
                "database commit failure with secret test value"
            )
        self.committed = True
        self.transaction_inserted_keys.clear()

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
        lambda: SimpleNamespace(webhook_token="secret-token", env="sandbox"),
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
    assert response["audit"]["provider"] == "asaas"
    assert response["audit"]["environment"] == "sandbox"
    assert response["audit"]["source"] == "asaas_sandbox_webhook_receiver"
    assert response["audit"]["audit_status"] == "asaas_sandbox_webhook_recorded"
    assert response["audit"]["event_accepted"] is True
    assert response["audit"]["payment_id_present"] is True
    assert response["audit"]["storage"]["raw_payload_stored"] is False
    assert response["audit"]["storage"]["raw_event_id_stored"] is False
    assert response["audit"]["storage"]["raw_payment_id_stored"] is False
    assert response["audit"]["can_credit_balance"] is False
    assert response["audit"]["can_generate_real_receipt"] is False
    assert response["audit"]["can_mark_real_paid"] is False
    assert next(iter(db.records.values())).status_code == 200
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

    encoded = json.dumps(second, ensure_ascii=False, default=str)

    assert first["duplicated"] is False
    assert second["duplicated"] is True
    assert second["idempotency"]["replayed"] is True
    assert second["idempotency"]["state"] == "replayed"
    assert (
        second["idempotency"]["replay_audit_status"]
        == "asaas_sandbox_webhook_idempotent_replay"
    )
    assert second["audit"]["replay"]["replay_status"] == (
        "asaas_sandbox_webhook_idempotent_replay"
    )
    assert second["audit"]["replay"]["safe_replay"] is True
    assert second["audit"]["replay"]["duplicated"] is True
    assert second["audit"]["replay"]["idempotency_replayed"] is True
    assert second["audit"]["replay"]["raw_payload_stored"] is False
    assert second["audit"]["replay"]["raw_event_id_stored"] is False
    assert second["audit"]["replay"]["raw_payment_id_stored"] is False
    assert second["audit"]["replay"]["can_credit_balance"] is False
    assert second["audit"]["replay"]["can_generate_real_receipt"] is False
    assert second["audit"]["replay"]["can_mark_real_paid"] is False
    assert second["can_credit_balance"] is False
    assert second["can_generate_real_receipt"] is False
    assert second["can_mark_real_paid"] is False
    assert "secret-token" not in encoded
    assert "pay_real_sandbox_must_not_leak" not in encoded
    assert "evt_test_unique_001" not in encoded
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
    assert response["audit"]["audit_status"] == "asaas_sandbox_webhook_ignored_recorded"
    assert response["audit"]["event_accepted"] is False
    assert response["audit"]["storage"]["raw_payload_stored"] is False
    assert "pay_created_must_not_leak" not in encoded



def test_asaas_sandbox_webhook_registers_panel_fallback_routes():
    paths = {
        route.path
        for route in wallet_routes.router.routes
        if getattr(route, "endpoint", None)
        is wallet_routes.handle_asaas_sandbox_webhook_receiver
    }

    assert "/api/v1/partners/asaas/webhooks/sandbox" in paths
    assert "/api/v1/partners/" in paths
    assert "/api/v1/partners" in paths


def test_asaas_sandbox_webhook_audit_history_lists_safe_records_without_sensitive_values():
    db = FakeDb()

    wallet_routes.handle_asaas_sandbox_webhook_receiver(
        payload=_valid_payload(),
        db=db,
        asaas_access_token="secret-token",
    )

    response = wallet_routes.get_asaas_sandbox_webhook_audit_history(
        limit=20,
        current_user=SimpleNamespace(id=123),
        db=db,
    )

    encoded = json.dumps(response, ensure_ascii=False, default=str)

    assert response["ok"] is True
    assert response["history"]["provider"] == "asaas"
    assert response["history"]["environment"] == "sandbox"
    assert response["history"]["source"] == "idempotency_keys"
    assert response["history"]["total_returned"] == 1
    assert response["wallet"]["provider"] == "asaas"
    assert response["wallet"]["real_money_enabled"] is False
    assert response["can_credit_balance"] is False
    assert response["can_generate_real_receipt"] is False
    assert response["can_mark_real_paid"] is False

    item = response["items"][0]
    assert item["provider"] == "asaas"
    assert item["environment"] == "sandbox"
    assert item["event_type"] == "PAYMENT_RECEIVED"
    assert item["event_accepted"] is True
    assert item["payment_id_present"] is True
    assert item["audit_status"] == "asaas_sandbox_webhook_recorded"
    assert item["storage"]["raw_payload_stored"] is False
    assert item["storage"]["raw_event_id_stored"] is False
    assert item["storage"]["raw_payment_id_stored"] is False
    assert item["can_credit_balance"] is False
    assert item["can_generate_real_receipt"] is False
    assert item["can_mark_real_paid"] is False

    assert "secret-token" not in encoded
    assert "pay_real_sandbox_must_not_leak" not in encoded
    assert "evt_test_unique_001" not in encoded


def test_asaas_sandbox_webhook_audit_history_ignores_malformed_or_non_asaas_records():
    db = FakeDb()

    wallet_routes.handle_asaas_sandbox_webhook_receiver(
        payload=_valid_payload(),
        db=db,
        asaas_access_token="secret-token",
    )

    good_key = next(iter(db.records))
    good_record = db.records[good_key]

    malformed = SimpleNamespace(
        key="asaas-sandbox-webhook:malformed",
        request_hash="bad",
        status_code=200,
        created_at=good_record.created_at,
        response_json="{not-json",
    )
    non_asaas = SimpleNamespace(
        key="asaas-sandbox-webhook:non-asaas",
        request_hash="non-asaas",
        status_code=200,
        created_at=good_record.created_at,
        response_json=json.dumps({
            "audit": {
                "provider": "other",
                "environment": "sandbox",
            }
        }),
    )

    db.records[malformed.key] = malformed
    db.records[non_asaas.key] = non_asaas

    items = wallet_routes._list_asaas_sandbox_webhook_audit_events(db, limit=20)

    assert len(items) == 1
    assert items[0]["provider"] == "asaas"
    assert items[0]["event_type"] == "PAYMENT_RECEIVED"



def test_asaas_sandbox_webhook_returns_503_for_incomplete_duplicate():
    db = FakeDb()
    payload = _valid_payload()
    event_id = wallet_routes._asaas_sandbox_webhook_event_id(payload)
    idem_key = wallet_routes._asaas_sandbox_webhook_idempotency_key(
        event_id
    )
    request_hash = wallet_routes._asaas_sandbox_webhook_hash(payload)

    db.records[idem_key] = SimpleNamespace(
        key=idem_key,
        request_hash=request_hash,
        status_code=None,
        response_json=None,
        created_at=None,
    )

    with pytest.raises(HTTPException) as exc:
        wallet_routes.handle_asaas_sandbox_webhook_receiver(
            payload=payload,
            db=db,
            asaas_access_token="secret-token",
        )

    rendered = json.dumps(
        {
            "detail": exc.value.detail,
            "headers": exc.value.headers,
        },
        ensure_ascii=False,
    )

    assert exc.value.status_code == 503
    assert exc.value.headers == {"Retry-After": "30"}
    assert db.rolled_back is True
    assert db.committed is False
    assert idem_key in db.records
    assert "secret-token" not in rendered
    assert "evt_test_unique_001" not in rendered
    assert "pay_real_sandbox_must_not_leak" not in rendered


def test_asaas_sandbox_webhook_commit_failure_rolls_back_and_returns_503():
    db = FakeDb(fail_commit=True)

    with pytest.raises(HTTPException) as exc:
        wallet_routes.handle_asaas_sandbox_webhook_receiver(
            payload=_valid_payload(),
            db=db,
            asaas_access_token="secret-token",
        )

    rendered = json.dumps(
        {
            "detail": exc.value.detail,
            "headers": exc.value.headers,
        },
        ensure_ascii=False,
    )

    assert exc.value.status_code == 503
    assert exc.value.headers == {"Retry-After": "30"}
    assert db.rolled_back is True
    assert db.committed is False
    assert db.records == {}
    assert "database commit failure" not in rendered
    assert "secret test value" not in rendered
    assert "secret-token" not in rendered
    assert "evt_test_unique_001" not in rendered
    assert "pay_real_sandbox_must_not_leak" not in rendered
