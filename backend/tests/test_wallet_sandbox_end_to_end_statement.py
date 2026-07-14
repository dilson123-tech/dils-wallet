import json
import os
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

from sqlalchemy.exc import IntegrityError

from app.api.v1.routes import wallet as wallet_routes
from app.partner import PixPaymentRequest, SandboxPartnerAdapter
from app.partner.asaas_payment_correlation import (
    build_asaas_payment_user_correlation_record,
)


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
        if self.row_limit is not None:
            rows = rows[: self.row_limit]
        return rows


class FakeDb:
    def __init__(self):
        self.records = {}
        self.pending = None
        self.transaction_inserted_keys = []

    def add(self, record):
        self.pending = record

    def flush(self):
        if self.pending.key in self.records:
            raise IntegrityError("duplicate", {}, Exception("duplicate"))

        key = self.pending.key
        self.records[key] = self.pending
        self.transaction_inserted_keys.append(key)
        self.pending = None

    def rollback(self):
        self.pending = None
        for key in self.transaction_inserted_keys:
            self.records.pop(key, None)
        self.transaction_inserted_keys.clear()

    def commit(self):
        self.transaction_inserted_keys.clear()

    def query(self, _model):
        return FakeQuery(self)


def _configure_sandbox(monkeypatch):
    adapter = SandboxPartnerAdapter()

    monkeypatch.setattr(wallet_routes, "WALLET_MODE", "partner")
    monkeypatch.setattr(wallet_routes, "IS_PARTNER_WALLET", True)
    monkeypatch.setattr(
        wallet_routes,
        "get_partner_adapter",
        lambda: adapter,
    )
    monkeypatch.setattr(
        wallet_routes,
        "create_partner_pix_payment",
        lambda **kwargs: adapter.create_pix_payment(
            PixPaymentRequest(
                user_id=kwargs["user_id"],
                amount=Decimal(kwargs["amount"]),
                description=kwargs["description"],
                external_id=kwargs["external_id"],
            )
        ),
    )
    monkeypatch.setattr(
        wallet_routes,
        "handle_partner_wallet_webhook",
        adapter.handle_webhook,
    )
    monkeypatch.setattr(
        wallet_routes,
        "get_partner_wallet_statement",
        lambda **_kwargs: [],
    )


def test_wallet_sandbox_end_to_end_payment_webhook_statement(monkeypatch):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user = SimpleNamespace(id=321)

    payment = wallet_routes.create_wallet_pix_sandbox_payment(
        payload=wallet_routes.WalletPixSandboxPaymentIn(
            amount=Decimal("99.90"),
            description="Fluxo ponta a ponta Sandbox",
            external_id="e2e-payment-001",
        ),
        current_user=user,
    )

    provider_reference = payment["payment"]["provider_reference"]

    assert provider_reference == "e2e-payment-001"
    assert payment["payment"]["status"] == "pending"
    assert (
        payment["payment"]["qr_code"]
        == "SANDBOX_QR_CODE_NOT_FOR_REAL_PAYMENT"
    )
    assert payment["wallet"]["real_money_enabled"] is False

    webhook_payload = wallet_routes.WalletPixSandboxWebhookIn(
        provider_reference=provider_reference,
        event_type="pix.payment.confirmed",
        status="confirmed",
        amount=Decimal("99.90"),
        idempotency_key="e2e-webhook-001",
        raw={"provider_secret": "must-not-leak"},
    )

    first = wallet_routes.handle_wallet_pix_sandbox_webhook(
        payload=webhook_payload,
        current_user=user,
        db=db,
        x_idempotency_key="e2e-webhook-001",
    )
    replay = wallet_routes.handle_wallet_pix_sandbox_webhook(
        payload=webhook_payload,
        current_user=user,
        db=db,
        x_idempotency_key="e2e-webhook-001",
    )

    statement = wallet_routes.get_wallet_structured_statement(
        limit=50,
        current_user=user,
        db=db,
    )

    assert first["duplicated"] is False
    assert first["user_id"] == 321
    assert first["can_credit_balance"] is False
    assert replay["duplicated"] is True
    assert replay["idempotency"]["replayed"] is True

    assert statement["statement"]["count"] == 1
    assert statement["wallet"]["provider"] == "sandbox"
    assert statement["wallet"]["source"] == "sandbox"
    assert statement["wallet"]["real_money_enabled"] is False

    item = statement["statement"]["items"][0]

    assert item == {
        "provider_reference": "e2e-payment-001",
        "direction": "credit",
        "amount": "99.90",
        "status": "confirmed",
        "description": "PIX sandbox confirmado",
        "created_at": first["event"]["received_at"],
        "source": "sandbox",
        "real_money_enabled": False,
    }

    rendered = json.dumps(
        {
            "payment": payment,
            "statement": statement,
        },
        ensure_ascii=False,
        default=str,
    )

    assert "must-not-leak" not in rendered
    assert "provider_secret" not in rendered


def test_sandbox_statement_does_not_mix_events_between_users(monkeypatch):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    first_user = SimpleNamespace(id=321)
    second_user = SimpleNamespace(id=654)

    wallet_routes.handle_wallet_pix_sandbox_webhook(
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="private-user-321-payment",
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("25.00"),
            idempotency_key="private-user-321-event",
        ),
        current_user=first_user,
        db=db,
        x_idempotency_key="private-user-321-event",
    )

    second_statement = wallet_routes.get_wallet_structured_statement(
        limit=50,
        current_user=second_user,
        db=db,
    )

    assert second_statement["statement"]["count"] == 0
    assert second_statement["statement"]["items"] == []
    assert second_statement["wallet"]["real_money_enabled"] is False

def test_asaas_correlated_payment_received_projects_once_to_statement(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)
    monkeypatch.setattr(
        wallet_routes,
        "load_asaas_sandbox_config",
        lambda: SimpleNamespace(
            webhook_token="secret-token",
            env="sandbox",
        ),
    )

    db = FakeDb()
    owner = SimpleNamespace(id=321)
    other_user = SimpleNamespace(id=654)
    external_reference = f"agpay_{'a' * 32}"

    correlation_record = (
        build_asaas_payment_user_correlation_record(
            user_id=owner.id,
            external_reference=external_reference,
        )
    )
    db.records[correlation_record.key] = correlation_record

    payload = {
        "id": "evt_statement_projection_001",
        "event": "PAYMENT_RECEIVED",
        "payment": {
            "id": "pay_statement_projection_must_not_leak",
            "status": "RECEIVED",
            "billingType": "PIX",
            "externalReference": external_reference,
            "value": 47.30,
        },
    }

    first = (
        wallet_routes.handle_asaas_sandbox_webhook_receiver(
            payload=payload,
            db=db,
            asaas_access_token="secret-token",
        )
    )
    replay = (
        wallet_routes.handle_asaas_sandbox_webhook_receiver(
            payload=payload,
            db=db,
            asaas_access_token="secret-token",
        )
    )

    owner_statement = (
        wallet_routes.get_wallet_structured_statement(
            limit=50,
            current_user=owner,
            db=db,
        )
    )
    other_statement = (
        wallet_routes.get_wallet_structured_statement(
            limit=50,
            current_user=other_user,
            db=db,
        )
    )

    assert first["duplicated"] is False
    assert first["can_credit_balance"] is False
    assert replay["duplicated"] is True
    assert replay["idempotency"]["replayed"] is True

    assert owner_statement["statement"]["count"] == 1
    assert other_statement["statement"]["count"] == 0
    assert (
        owner_statement["wallet"]["real_money_enabled"]
        is False
    )

    item = owner_statement["statement"]["items"][0]

    assert item["provider_reference"].startswith(
        "asaas-sandbox-payment-"
    )
    assert item["direction"] == "credit"
    assert item["amount"] == "47.30"
    assert item["status"] == "confirmed"
    assert (
        item["description"]
        == "PIX Asaas Sandbox recebido"
    )
    assert item["source"] == "sandbox"
    assert item["real_money_enabled"] is False

    rendered = json.dumps(
        owner_statement,
        ensure_ascii=False,
        default=str,
    )

    assert external_reference not in rendered
    assert (
        "pay_statement_projection_must_not_leak"
        not in rendered
    )
    assert "correlation_key" not in rendered
    assert "user_id" not in item


def test_asaas_unresolved_or_amountless_event_is_not_projected(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)
    monkeypatch.setattr(
        wallet_routes,
        "load_asaas_sandbox_config",
        lambda: SimpleNamespace(
            webhook_token="secret-token",
            env="sandbox",
        ),
    )

    db = FakeDb()
    user = SimpleNamespace(id=321)

    unresolved_payload = {
        "id": "evt_statement_unresolved_001",
        "event": "PAYMENT_RECEIVED",
        "payment": {
            "id": "pay_unresolved_must_not_leak",
            "status": "RECEIVED",
            "billingType": "PIX",
            "externalReference": f"agpay_{'b' * 32}",
            "value": 25.00,
        },
    }

    wallet_routes.handle_asaas_sandbox_webhook_receiver(
        payload=unresolved_payload,
        db=db,
        asaas_access_token="secret-token",
    )

    correlated_reference = f"agpay_{'c' * 32}"
    correlation_record = (
        build_asaas_payment_user_correlation_record(
            user_id=user.id,
            external_reference=correlated_reference,
        )
    )
    db.records[correlation_record.key] = correlation_record

    amountless_payload = {
        "id": "evt_statement_amountless_001",
        "event": "PAYMENT_RECEIVED",
        "payment": {
            "id": "pay_amountless_must_not_leak",
            "status": "RECEIVED",
            "billingType": "PIX",
            "externalReference": correlated_reference,
        },
    }

    wallet_routes.handle_asaas_sandbox_webhook_receiver(
        payload=amountless_payload,
        db=db,
        asaas_access_token="secret-token",
    )

    statement = wallet_routes.get_wallet_structured_statement(
        limit=50,
        current_user=user,
        db=db,
    )

    assert statement["statement"]["count"] == 0
    assert statement["statement"]["items"] == []
    assert statement["wallet"]["real_money_enabled"] is False
