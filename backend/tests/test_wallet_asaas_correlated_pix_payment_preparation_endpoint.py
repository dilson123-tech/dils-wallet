import json
import os
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.requests import Request as StarletteRequest

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


def _make_prepare_endpoint_request(client_host: str) -> StarletteRequest:
    """
    Request ASGI mínimo e determinístico para exercitar diretamente
    prepare_wallet_asaas_correlated_pix_payment neste teste, agora que a
    função é decorada com @limiter.limit("10/minute") e o wrapper do
    SlowAPI exige um starlette.requests.Request real em toda chamada
    (HTTP real ou direta). Mesmo padrão de
    test_wallet_sandbox_end_to_end_statement.py::_make_sandbox_wallet_request.

    client_host é fixo/escolhido por FUNÇÃO de teste (nunca reaproveitado
    entre funções de teste diferentes). Cada chamada ao handler decorado
    invoca este helper de novo para obter uma instância NOVA de Request
    -- nunca reaproveitar o mesmo objeto entre duas chamadas, pois o
    SlowAPI marca request.state._rate_limiting_complete na primeira
    checagem, e uma segunda chamada com o MESMO objeto Request pularia
    silenciosamente a checagem do limiter.
    """
    path = "/api/v1/wallet/pix/asaas/sandbox/prepare"
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
    due_date="2026-07-30",
    description="Cobrança correlacionada via endpoint",
):
    return (
        wallet_routes
        .WalletAsaasCorrelatedPixPaymentPreparationIn(
            customer_id=customer_id,
            amount=amount,
            due_date=due_date,
            description=description,
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
            request=_make_prepare_endpoint_request("198.51.101.1"),
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
            request=_make_prepare_endpoint_request("198.51.101.2"),
            payload=payload,
            current_user=user,
            db=db,
        )
    )
    replay = (
        wallet_routes
        .prepare_wallet_asaas_correlated_pix_payment(
            request=_make_prepare_endpoint_request("198.51.101.2"),
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
        request=_make_prepare_endpoint_request("198.51.101.3"),
        payload=_payload(amount=Decimal("10.00")),
        current_user=user,
        db=db,
    )

    with pytest.raises(HTTPException) as captured:
        wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
            request=_make_prepare_endpoint_request("198.51.101.3"),
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
            request=_make_prepare_endpoint_request("198.51.101.4"),
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
            request=_make_prepare_endpoint_request("198.51.101.5"),
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
            request=_make_prepare_endpoint_request("198.51.101.6"),
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
            request=_make_prepare_endpoint_request("198.51.101.7"),
            payload=_payload(),
            current_user=SimpleNamespace(id=321),
            db=FakeDb(),
        )

    assert captured.value.status_code == 503
    assert "sensitive config detail" not in str(
        captured.value.detail
    )


# ---------------------------------------------------------------------
# Limites de entrada (P0-A da auditoria de contenção de storage do
# Wallet Sandbox): customer_id/due_date/description agora são
# fail-closed via Field(max_length=...) no schema Pydantic -- acima do
# limite, a própria construção do payload levanta
# pydantic.ValidationError, ANTES de qualquer chamada ao
# handler/db.add/commit (nenhum truncamento silencioso). Nenhum destes
# campos termina persistido cru em response_json hoje, mas o limite de
# entrada segue contendo o custo transiente de CPU/parse por requisição.
# ---------------------------------------------------------------------


def test_endpoint_customer_id_max_length_boundary(monkeypatch):
    _configure_sandbox(monkeypatch)

    external_reference = f"agpay_{'e' * 32}"
    monkeypatch.setattr(
        correlated_service,
        "generate_asaas_payment_external_reference",
        lambda: external_reference,
    )

    db = FakeDb()
    exactly_64 = "c" * 64

    response = wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
        request=_make_prepare_endpoint_request("198.51.101.8"),
        payload=_payload(customer_id=exactly_64),
        current_user=SimpleNamespace(id=321),
        db=db,
    )
    assert response["ok"] is True
    assert len(db.records) == 1

    over_65 = "c" * 65
    with pytest.raises(ValidationError):
        _payload(customer_id=over_65)

    # payload de 65 caracteres nunca chegou a existir -> nenhuma linha
    # nova foi (nem poderia ter sido) criada.
    assert len(db.records) == 1


def test_endpoint_due_date_max_length_boundary(monkeypatch):
    _configure_sandbox(monkeypatch)

    external_reference = f"agpay_{'f' * 32}"
    monkeypatch.setattr(
        correlated_service,
        "generate_asaas_payment_external_reference",
        lambda: external_reference,
    )

    db = FakeDb()
    # due_date não tem validação semântica de formato de data hoje
    # (_required_text só exige não-vazio) -- uma string arbitrária de 32
    # caracteres é, portanto, um caso válido real para testar o
    # max_length sem enfraquecer nenhuma validação existente.
    exactly_32 = "2026-07-30 " + ("d" * 21)
    assert len(exactly_32) == 32

    response = wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
        request=_make_prepare_endpoint_request("198.51.101.9"),
        payload=_payload(due_date=exactly_32),
        current_user=SimpleNamespace(id=321),
        db=db,
    )
    assert response["ok"] is True
    assert len(db.records) == 1

    over_33 = exactly_32 + "x"
    assert len(over_33) == 33
    with pytest.raises(ValidationError):
        _payload(due_date=over_33)

    assert len(db.records) == 1


def test_endpoint_description_max_length_boundary(monkeypatch):
    _configure_sandbox(monkeypatch)

    external_reference = f"agpay_{'0' * 32}"
    monkeypatch.setattr(
        correlated_service,
        "generate_asaas_payment_external_reference",
        lambda: external_reference,
    )

    db = FakeDb()
    exactly_200 = "d" * 200

    response = wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
        request=_make_prepare_endpoint_request("198.51.101.10"),
        payload=_payload(description=exactly_200),
        current_user=SimpleNamespace(id=321),
        db=db,
    )
    assert response["ok"] is True
    assert len(db.records) == 1

    over_201 = "d" * 201
    with pytest.raises(ValidationError):
        _payload(description=over_201)

    assert len(db.records) == 1
