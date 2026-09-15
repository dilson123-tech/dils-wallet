import json
import os
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request as StarletteRequest

from app.api.v1.routes import wallet as wallet_routes
from app.services import sandbox_namespace_cap as _sandbox_namespace_cap_module
from app.partner import InternalSandboxPartnerAdapter, PixPaymentRequest
from app.partner.asaas_payment_correlation import (
    build_asaas_payment_user_correlation_record,
)


def _make_partner_webhook_request(client_host: str, *, path: str = "/api/v1/partners") -> StarletteRequest:
    """
    Request ASGI mínimo e determinístico para exercitar diretamente
    handle_asaas_sandbox_webhook_receiver neste teste, agora que a função
    é decorada com @limiter.shared_limit(...) e o wrapper do SlowAPI
    exige um starlette.requests.Request real em toda chamada (HTTP real
    ou direta). client_host é fixo/escolhido pelo próprio teste -- nunca
    lido de X-Forwarded-For -- e isolado dos hosts já usados em
    test_asaas_webhook_receiver.py, evitando colisão de orçamento.
    """
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": (client_host, 12345),
        "scheme": "http",
        "app": None,
    }
    return StarletteRequest(scope)


def _make_sandbox_wallet_request(
    client_host: str, *, method: str = "POST", path: str
) -> StarletteRequest:
    """
    Request ASGI mínimo e determinístico para exercitar diretamente os
    handlers Wallet PIX Sandbox (sandbox-payment, sandbox-webhook,
    sandbox-reconciliation, sandbox-audit-history) neste teste, agora
    que cada um é decorado com @limiter.limit(...) individual e o
    wrapper do SlowAPI exige um starlette.requests.Request real em toda
    chamada (HTTP real ou direta). Mesmo padrão de
    _make_partner_webhook_request, generalizado para GET/POST.

    client_host é fixo/escolhido por FUNÇÃO de teste (nunca reaproveitado
    entre funções de teste diferentes, para não acumular orçamento entre
    elas). Cada chamada ao handler decorado, porém, deve invocar este
    helper de novo para obter uma instância NOVA de Request -- nunca
    reaproveitar o mesmo objeto entre duas chamadas, pois o SlowAPI marca
    request.state._rate_limiting_complete na primeira checagem, e uma
    segunda chamada com o MESMO objeto Request pularia silenciosamente a
    checagem do limiter.
    """
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": (client_host, 12345),
        "scheme": "http",
        "app": None,
    }
    return StarletteRequest(scope)


class FakeQuery:
    def __init__(self, db):
        self.db = db
        self.key = None
        self.row_limit = None
        self.like_prefix = None

    def filter_by(self, **kwargs):
        self.key = kwargs.get("key")
        return self

    def filter(self, *args, **_kwargs):
        # Captura o prefixo de IdempotencyKey.key.like("<prefixo>%"),
        # a mesma expressão usada pela produção -- sem isso, count()
        # não reproduziria fielmente o WHERE key LIKE '<namespace>:%'
        # real, e poderia esconder um count() que soma namespaces
        # diferentes por engano.
        for arg in args:
            pattern = getattr(getattr(arg, "right", None), "value", None)
            if isinstance(pattern, str) and pattern.endswith("%"):
                self.like_prefix = pattern[:-1]
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

    def count(self):
        if self.like_prefix is None:
            return len(self.db.records)
        return len(
            [
                row
                for row in self.db.records.values()
                if str(row.key).startswith(self.like_prefix)
            ]
        )


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
    adapter = InternalSandboxPartnerAdapter()

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
        request=_make_sandbox_wallet_request(
            "198.51.100.1", path="/api/v1/wallet/pix/sandbox-payment"
        ),
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
        request=_make_sandbox_wallet_request(
            "198.51.100.1", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=webhook_payload,
        current_user=user,
        db=db,
        x_idempotency_key="e2e-webhook-001",
    )
    replay = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.1", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
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
        request=_make_sandbox_wallet_request(
            "198.51.100.2", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
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
            request=_make_partner_webhook_request("203.0.113.21"),
            payload=payload,
            db=db,
            asaas_access_token="secret-token",
        )
    )
    replay = (
        wallet_routes.handle_asaas_sandbox_webhook_receiver(
            request=_make_partner_webhook_request("203.0.113.21"),
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
        request=_make_partner_webhook_request("203.0.113.22"),
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
        request=_make_partner_webhook_request("203.0.113.22"),
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


# ---------------------------------------------------------------------
# Isolamento cross-customer do Wallet PIX Sandbox (idempotência do
# webhook, reconciliation e audit-history). Ver investigação/design
# dedicados desta sessão: a chave de idempotência do webhook agora é
# namespaced por user_id (sha256(f"{user_id}|{raw_key}")), e os dois
# consumidores de leitura (reconciliation, audit-history) só devolvem
# eventos cujo response_json["user_id"] bate com o usuário autenticado
# -- campo sempre gravado server-side, nunca vindo do payload/header do
# cliente. Registros legados sem esse campo nunca são retornados
# (fail-closed), sem tentar adivinhar a quem pertenciam.
# ---------------------------------------------------------------------


def test_sandbox_webhook_idempotency_key_is_scoped_per_user(monkeypatch):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user_a = SimpleNamespace(id=111)
    user_b = SimpleNamespace(id=222)

    shared_raw_key = "shared-raw-idempotency-key"

    payload_a = wallet_routes.WalletPixSandboxWebhookIn(
        provider_reference="user-a-ref",
        event_type="pix.payment.confirmed",
        status="confirmed",
        amount=Decimal("10.00"),
        idempotency_key=shared_raw_key,
    )

    # 1) mesmo usuário + mesma chave + mesmo payload => replay correto.
    first_a = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.3", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=payload_a,
        current_user=user_a,
        db=db,
        x_idempotency_key=shared_raw_key,
    )
    replay_a = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.3", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=payload_a,
        current_user=user_a,
        db=db,
        x_idempotency_key=shared_raw_key,
    )

    assert first_a["duplicated"] is False
    assert first_a["user_id"] == 111
    assert replay_a["duplicated"] is True
    assert replay_a["idempotency"]["replayed"] is True

    # 2) mesmo usuário + mesma chave + payload diferente => 409.
    payload_a_different = wallet_routes.WalletPixSandboxWebhookIn(
        provider_reference="user-a-ref-different",
        event_type="pix.payment.confirmed",
        status="confirmed",
        amount=Decimal("10.00"),
        idempotency_key=shared_raw_key,
    )

    try:
        wallet_routes.handle_wallet_pix_sandbox_webhook(
            request=_make_sandbox_wallet_request(
                "198.51.100.3", path="/api/v1/wallet/pix/sandbox-webhook"
            ),
            payload=payload_a_different,
            current_user=user_a,
            db=db,
            x_idempotency_key=shared_raw_key,
        )
        raise AssertionError("esperava HTTPException 409 para payload divergente")
    except HTTPException as exc:
        assert exc.status_code == 409

    # 3) usuário DIFERENTE usando a MESMA raw key => operação
    # independente, sem IntegrityError entre usuários, sem replay
    # cruzado (duplicated=False, é um evento novo e próprio de B).
    payload_b = wallet_routes.WalletPixSandboxWebhookIn(
        provider_reference="user-b-ref",
        event_type="pix.payment.confirmed",
        status="confirmed",
        amount=Decimal("20.00"),
        idempotency_key=shared_raw_key,
    )

    first_b = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.3", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=payload_b,
        current_user=user_b,
        db=db,
        x_idempotency_key=shared_raw_key,
    )

    assert first_b["duplicated"] is False
    assert first_b["user_id"] == 222
    assert first_b["event"]["provider_reference"] == "user-b-ref"


def test_sandbox_reconciliation_is_scoped_per_user_and_ignores_legacy_records(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user_a = SimpleNamespace(id=333)
    user_b = SimpleNamespace(id=444)

    wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.4", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="private-ref-a",
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("15.00"),
            idempotency_key="reconciliation-key-a",
        ),
        current_user=user_a,
        db=db,
        x_idempotency_key="reconciliation-key-a",
    )

    # 5) A consulta a própria referência => encontra normalmente.
    own_reconciliation = wallet_routes.get_wallet_pix_sandbox_reconciliation(
        request=_make_sandbox_wallet_request(
            "198.51.100.4",
            method="GET",
            path="/api/v1/wallet/pix/sandbox-reconciliation/private-ref-a",
        ),
        provider_reference="private-ref-a",
        current_user=user_a,
        db=db,
    )
    assert own_reconciliation["reconciliation"]["event_found"] is True
    assert own_reconciliation["reconciliation"]["status"] == "confirmed"

    # 4) B tenta reconciliar a MESMA provider_reference de A => não
    # recebe o evento de A (mesmo formato de "não encontrado").
    cross_reconciliation = wallet_routes.get_wallet_pix_sandbox_reconciliation(
        request=_make_sandbox_wallet_request(
            "198.51.100.4",
            method="GET",
            path="/api/v1/wallet/pix/sandbox-reconciliation/private-ref-a",
        ),
        provider_reference="private-ref-a",
        current_user=user_b,
        db=db,
    )
    assert cross_reconciliation["reconciliation"]["event_found"] is False
    assert cross_reconciliation["reconciliation"]["status"] == "not_found"

    # 6) registro legado (sem "user_id" no response_json, simulando um
    # evento anterior a este isolamento) nunca é devolvido a ninguém.
    legacy_response = {
        "ok": True,
        "duplicated": False,
        "event": {
            "provider": "sandbox",
            "provider_reference": "legacy-ref-no-owner",
            "event_type": "pix.payment.confirmed",
            "status": "confirmed",
            "amount": "5.00",
            "received_at": "2026-01-01T00:00:00+00:00",
        },
        # Deliberadamente sem "user_id".
    }
    legacy_key = "wallet-sandbox-webhook:legacy-digest-without-owner"
    db.records[legacy_key] = SimpleNamespace(
        key=legacy_key,
        request_hash="legacy-hash",
        status_code=200,
        response_json=json.dumps(legacy_response),
        created_at=None,
    )

    legacy_for_a = wallet_routes.get_wallet_pix_sandbox_reconciliation(
        request=_make_sandbox_wallet_request(
            "198.51.100.4",
            method="GET",
            path="/api/v1/wallet/pix/sandbox-reconciliation/legacy-ref-no-owner",
        ),
        provider_reference="legacy-ref-no-owner",
        current_user=user_a,
        db=db,
    )
    legacy_for_b = wallet_routes.get_wallet_pix_sandbox_reconciliation(
        request=_make_sandbox_wallet_request(
            "198.51.100.4",
            method="GET",
            path="/api/v1/wallet/pix/sandbox-reconciliation/legacy-ref-no-owner",
        ),
        provider_reference="legacy-ref-no-owner",
        current_user=user_b,
        db=db,
    )

    assert legacy_for_a["reconciliation"]["event_found"] is False
    assert legacy_for_b["reconciliation"]["event_found"] is False


def test_sandbox_audit_history_is_scoped_per_user_and_ignores_legacy_records(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user_a = SimpleNamespace(id=555)
    user_b = SimpleNamespace(id=666)

    wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.5", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="audit-ref-a",
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("30.00"),
            idempotency_key="audit-key-a",
        ),
        current_user=user_a,
        db=db,
        x_idempotency_key="audit-key-a",
    )
    wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.5", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="audit-ref-b",
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("40.00"),
            idempotency_key="audit-key-b",
        ),
        current_user=user_b,
        db=db,
        x_idempotency_key="audit-key-b",
    )

    # registro legado sem "user_id" no response_json.
    legacy_response = {
        "event": {
            "provider_reference": "audit-ref-legacy",
            "event_type": "pix.payment.confirmed",
            "status": "confirmed",
        },
    }
    legacy_key = "wallet-sandbox-webhook:legacy-digest-audit"
    db.records[legacy_key] = SimpleNamespace(
        key=legacy_key,
        request_hash="legacy-hash-audit",
        status_code=200,
        response_json=json.dumps(legacy_response),
        created_at=None,
    )

    # 7/8) cada usuário vê somente os próprios eventos.
    history_a = wallet_routes.get_wallet_pix_sandbox_audit_history(
        request=_make_sandbox_wallet_request(
            "198.51.100.5",
            method="GET",
            path="/api/v1/wallet/pix/sandbox-audit-history",
        ),
        limit=20,
        current_user=user_a,
        db=db,
    )
    history_b = wallet_routes.get_wallet_pix_sandbox_audit_history(
        request=_make_sandbox_wallet_request(
            "198.51.100.5",
            method="GET",
            path="/api/v1/wallet/pix/sandbox-audit-history",
        ),
        limit=20,
        current_user=user_b,
        db=db,
    )

    refs_a = {item["provider_reference"] for item in history_a["items"]}
    refs_b = {item["provider_reference"] for item in history_b["items"]}

    assert refs_a == {"audit-ref-a"}
    assert refs_b == {"audit-ref-b"}

    # 9) o registro legado nunca aparece, para nenhum dos dois usuários.
    assert "audit-ref-legacy" not in refs_a
    assert "audit-ref-legacy" not in refs_b


# ---------------------------------------------------------------------
# Limites de entrada (P0-A da auditoria de contenção de storage do
# Wallet Sandbox): provider_reference/event_type/idempotency_key (body)
# do webhook PIX sandbox agora são fail-closed via Field(max_length=...)
# no schema Pydantic -- acima do limite, a própria construção do payload
# levanta pydantic.ValidationError, ANTES de qualquer chamada ao
# handler/hash/query/insert (nenhum truncamento silencioso). O header
# Idempotency-Key não passa pelo schema do body, então tem checagem
# manual equivalente dentro do handler (HTTPException 422).
# ---------------------------------------------------------------------


def test_sandbox_webhook_provider_reference_max_length_boundary(monkeypatch):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user = SimpleNamespace(id=771)

    exactly_80 = "r" * 80
    result = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.6", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference=exactly_80,
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("10.00"),
            idempotency_key="boundary-provider-ref-80",
        ),
        current_user=user,
        db=db,
        x_idempotency_key="boundary-provider-ref-80",
    )
    assert result["ok"] is True
    assert result["event"]["provider_reference"] == exactly_80
    assert len(db.records) == 1

    over_81 = "r" * 81
    try:
        wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference=over_81,
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("10.00"),
            idempotency_key="boundary-provider-ref-81",
        )
        raise AssertionError(
            "esperava ValidationError para provider_reference de 81 caracteres"
        )
    except ValidationError:
        pass

    # payload de 81 caracteres nunca chegou a existir -> nenhuma linha
    # nova foi (nem poderia ter sido) criada.
    assert len(db.records) == 1


def test_sandbox_webhook_event_type_max_length_boundary(monkeypatch):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user = SimpleNamespace(id=772)

    exactly_64 = "e" * 64
    result = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.7", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="boundary-event-type-64",
            event_type=exactly_64,
            status="confirmed",
            amount=Decimal("10.00"),
            idempotency_key="boundary-event-type-64",
        ),
        current_user=user,
        db=db,
        x_idempotency_key="boundary-event-type-64",
    )
    assert result["ok"] is True
    assert result["event"]["event_type"] == exactly_64
    assert len(db.records) == 1

    over_65 = "e" * 65
    try:
        wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="boundary-event-type-65",
            event_type=over_65,
            status="confirmed",
            amount=Decimal("10.00"),
            idempotency_key="boundary-event-type-65",
        )
        raise AssertionError(
            "esperava ValidationError para event_type de 65 caracteres"
        )
    except ValidationError:
        pass

    assert len(db.records) == 1


def test_sandbox_webhook_body_idempotency_key_max_length_boundary(monkeypatch):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user = SimpleNamespace(id=773)

    exactly_128 = "k" * 128
    result = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.8", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="boundary-body-key-128",
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("10.00"),
            idempotency_key=exactly_128,
        ),
        current_user=user,
        db=db,
        # Sem header -- força o handler a usar payload.idempotency_key
        # (o body de 128 caracteres) como raw_key.
        x_idempotency_key=None,
    )
    assert result["ok"] is True
    assert len(db.records) == 1

    over_129 = "k" * 129
    try:
        wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="boundary-body-key-129",
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("10.00"),
            idempotency_key=over_129,
        )
        raise AssertionError(
            "esperava ValidationError para idempotency_key (body) de 129 caracteres"
        )
    except ValidationError:
        pass

    assert len(db.records) == 1


def test_sandbox_webhook_header_idempotency_key_max_length_boundary(monkeypatch):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user = SimpleNamespace(id=774)

    exactly_128 = "h" * 128
    result = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.9", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="boundary-header-key-128",
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("10.00"),
        ),
        current_user=user,
        db=db,
        x_idempotency_key=exactly_128,
    )
    assert result["ok"] is True
    assert len(db.records) == 1

    over_129 = "h" * 129
    try:
        wallet_routes.handle_wallet_pix_sandbox_webhook(
            request=_make_sandbox_wallet_request(
                "198.51.100.9", path="/api/v1/wallet/pix/sandbox-webhook"
            ),
            payload=wallet_routes.WalletPixSandboxWebhookIn(
                provider_reference="boundary-header-key-129",
                event_type="pix.payment.confirmed",
                status="confirmed",
                amount=Decimal("10.00"),
            ),
            current_user=user,
            db=db,
            x_idempotency_key=over_129,
        )
        raise AssertionError(
            "esperava HTTPException 422 para header Idempotency-Key de 129 caracteres"
        )
    except HTTPException as exc:
        assert exc.status_code == 422

    # a checagem do header acontece ANTES de qualquer db.add/flush ->
    # continua exatamente 1 linha (a do caso válido de 128 acima).
    assert len(db.records) == 1


def test_sandbox_webhook_provider_reference_80_chars_remains_reconciliable(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)

    db = FakeDb()
    user = SimpleNamespace(id=775)

    provider_reference_80 = "z" * 80

    wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.10", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference=provider_reference_80,
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("10.00"),
            idempotency_key="reconciliation-boundary-80",
        ),
        current_user=user,
        db=db,
        x_idempotency_key="reconciliation-boundary-80",
    )

    reconciliation = wallet_routes.get_wallet_pix_sandbox_reconciliation(
        request=_make_sandbox_wallet_request(
            "198.51.100.10",
            method="GET",
            path=f"/api/v1/wallet/pix/sandbox-reconciliation/{provider_reference_80}",
        ),
        provider_reference=provider_reference_80,
        current_user=user,
        db=db,
    )

    assert reconciliation["reconciliation"]["event_found"] is True
    assert reconciliation["reconciliation"]["status"] == "confirmed"


# ---------------------------------------------------------------------
# Soft cap operacional de cardinalidade por namespace sandbox (P0-B):
# WALLET_SANDBOX_NAMESPACE_MAX_ROWS. Aqui provamos a integração ponta a
# ponta do endpoint B (chave nova rejeitada com 503 quando o namespace
# já está no limite, zero linha líquida nova, replay preservado mesmo
# com o namespace "cheio"). O cap em si (parsing, isolamento entre
# namespaces, segurança real-money) é testado isoladamente em
# test_wallet_sandbox_namespace_cap.py, com um SQLite real.
# ---------------------------------------------------------------------


def test_sandbox_webhook_new_key_rejected_when_namespace_cap_exceeded(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)
    monkeypatch.setattr(
        _sandbox_namespace_cap_module, "WALLET_SANDBOX_NAMESPACE_MAX_ROWS", 1
    )

    db = FakeDb()
    user = SimpleNamespace(id=881)

    first = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.20", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=wallet_routes.WalletPixSandboxWebhookIn(
            provider_reference="cap-boundary-a",
            event_type="pix.payment.confirmed",
            status="confirmed",
            amount=Decimal("10.00"),
            idempotency_key="cap-boundary-a",
        ),
        current_user=user,
        db=db,
        x_idempotency_key="cap-boundary-a",
    )
    assert first["ok"] is True
    assert len(db.records) == 1

    # chave NOVA (referência/idempotency_key diferentes) -> count
    # passaria a 2, acima do limite 1 -> 503, zero linha líquida nova.
    try:
        wallet_routes.handle_wallet_pix_sandbox_webhook(
            request=_make_sandbox_wallet_request(
                "198.51.100.20", path="/api/v1/wallet/pix/sandbox-webhook"
            ),
            payload=wallet_routes.WalletPixSandboxWebhookIn(
                provider_reference="cap-boundary-b",
                event_type="pix.payment.confirmed",
                status="confirmed",
                amount=Decimal("10.00"),
                idempotency_key="cap-boundary-b",
            ),
            current_user=user,
            db=db,
            x_idempotency_key="cap-boundary-b",
        )
        raise AssertionError(
            "esperava HTTPException 503 por soft cap de namespace excedido"
        )
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.headers.get("Retry-After") == "30"

    assert len(db.records) == 1


def test_sandbox_webhook_replay_still_works_when_namespace_cap_full(
    monkeypatch,
):
    _configure_sandbox(monkeypatch)
    monkeypatch.setattr(
        _sandbox_namespace_cap_module, "WALLET_SANDBOX_NAMESPACE_MAX_ROWS", 1
    )

    db = FakeDb()
    user = SimpleNamespace(id=882)

    payload = wallet_routes.WalletPixSandboxWebhookIn(
        provider_reference="cap-replay-a",
        event_type="pix.payment.confirmed",
        status="confirmed",
        amount=Decimal("10.00"),
        idempotency_key="cap-replay-a",
    )

    first = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.21", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=payload,
        current_user=user,
        db=db,
        x_idempotency_key="cap-replay-a",
    )
    assert first["duplicated"] is False
    assert len(db.records) == 1

    # replay da MESMA chave -- deve continuar funcionando normalmente,
    # mesmo com o namespace já "cheio" (limite=1, ocupado por essa
    # própria linha).
    replay = wallet_routes.handle_wallet_pix_sandbox_webhook(
        request=_make_sandbox_wallet_request(
            "198.51.100.21", path="/api/v1/wallet/pix/sandbox-webhook"
        ),
        payload=payload,
        current_user=user,
        db=db,
        x_idempotency_key="cap-replay-a",
    )
    assert replay["duplicated"] is True
    assert len(db.records) == 1


def test_fake_query_count_is_scoped_to_like_prefix_with_mixed_namespaces():
    """
    Prova de fidelidade do próprio FakeQuery/FakeDb usados acima: um
    FakeDb contendo registros de DOIS namespaces sandbox diferentes
    (mesma tabela compartilhada, igual à produção) não pode fazer
    count() de um namespace somar linhas do outro -- exatamente o
    WHERE key LIKE '<namespace>:%' real de
    enforce_sandbox_namespace_cap (app/services/sandbox_namespace_cap.py).
    """
    db = FakeDb()

    for i in range(3):
        key = f"wallet-sandbox-webhook:row-{i}"
        db.records[key] = SimpleNamespace(key=key)

    for i in range(5):
        key = f"asaas-payment-correlation:row-{i}"
        db.records[key] = SimpleNamespace(key=key)

    wallet_sandbox_count = (
        db.query(wallet_routes.IdempotencyKey)
        .filter(
            wallet_routes.IdempotencyKey.key.like(
                "wallet-sandbox-webhook:%"
            )
        )
        .count()
    )
    asaas_correlation_count = (
        db.query(wallet_routes.IdempotencyKey)
        .filter(
            wallet_routes.IdempotencyKey.key.like(
                "asaas-payment-correlation:%"
            )
        )
        .count()
    )

    assert wallet_sandbox_count == 3
    assert asaas_correlation_count == 5
