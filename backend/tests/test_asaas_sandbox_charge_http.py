"""
P0.4 — cobrança PIX real no Asaas SANDBOX (POST /payments + GET pixQrCode).

SQLite real em memória (StaticPool) para o service e o endpoint; o
transporte HTTP é sempre fake (callables injetados ou httpx.MockTransport).
Nenhum teste acessa a rede.

Garantias exercitadas:
- flag ASAAS_SANDBOX_CHARGE_HTTP_ENABLED ausente/!= "true" => endpoint
  idêntico ao da preparação local, sem HTTP;
- estado "attempted" persistido ANTES do POST: timeout, 5xx, resposta
  inválida ou falha ao persistir o payment_id nunca permitem um segundo
  POST para a mesma correlação;
- replay de cobrança criada só refaz o GET do QR;
- payment_id persistido na correlação e nunca devolvido na resposta;
- nenhuma resposta/exceção expõe a API key;
- transporte só fala com a base URL Sandbox, timeout de 10s, sem retry.
"""
import itertools
import json
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("SECRET_KEY", "asaas-sandbox-charge-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request as StarletteRequest

from app.api.v1.routes import wallet as wallet_routes
from app.core.rate_limit import limiter
from app.database import Base
from app.models.idempotency import IdempotencyKey
from app.models.user_main import User
from app.partner.asaas_client import AsaasSandboxClient
from app.partner.asaas_config import (
    ASAAS_PRODUCTION_BASE_URL,
    ASAAS_SANDBOX_BASE_URL,
    AsaasSandboxConfig,
)
from app.partner.asaas_http_transport import (
    ASAAS_SANDBOX_HTTP_TIMEOUT_SECONDS,
    AsaasSandboxHttpTransport,
    AsaasSandboxTransportError,
)
from app.partner.asaas_payment_correlation import (
    asaas_payment_correlation_key,
    resolve_asaas_payment_user_correlation,
)
from app.services import asaas_correlated_pix_payment_service as charge_service
from app.services.asaas_correlated_pix_payment_service import (
    ASAAS_WEBHOOK_CHARGE_CREDITABLE_STATUSES,
    AsaasCorrelatedPixChargeConflictError,
    AsaasCorrelatedPixChargeCustomerMismatchError,
    AsaasCorrelatedPixChargeIndeterminateError,
    AsaasCorrelatedPixChargePendingError,
    AsaasCorrelatedPixChargeProviderRejectedError,
    AsaasCorrelatedPixChargeProviderUnavailableError,
    AsaasCorrelatedPixPaymentConflictError,
    AsaasCorrelatedPixPaymentStorageError,
    apply_asaas_webhook_charge_transition,
    asaas_sandbox_customer_external_reference,
    create_asaas_correlated_pix_charge,
)

API_KEY = "charge-api-key-must-never-leak"
PREPARED_VALUE = "49.90"
PAYMENT_ID = "pay_sandbox0123456789"
QR_PAYLOAD = "00020101021226820014br.gov.bcb.pix2560sandbox-copia-e-cola"
QR_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
QR_EXPIRATION = "2026-12-31 23:59:59"
DUE_DATE = "2026-12-31"
DESCRIPTION = "Cobrança sandbox teste"
_CUSTOMER_PREFIX = "cus_sandboxuser"

TEST_CONFIG = AsaasSandboxConfig(
    env="sandbox",
    base_url=ASAAS_SANDBOX_BASE_URL,
    api_key=API_KEY,
    webhook_token="charge-webhook-token-must-never-leak",
    real_money_enabled=False,
    wallet_mode="partner",
    wallet_partner_provider="asaas",
)

_refs = itertools.count(1)
_hosts = itertools.count(1)


def _new_reference() -> str:
    return f"agpay_{next(_refs):032x}"


def _customer_id(user_id: int) -> str:
    return f"{_CUSTOMER_PREFIX}{user_id}"


def _owned_customer(request):
    """GET /customers/{id}: customer cujo externalReference prova o dono."""
    customer_id = request.url.rsplit("/", 1)[-1]
    owner = int(customer_id.removeprefix(_CUSTOMER_PREFIX))
    return (
        200,
        {
            "id": customer_id,
            "externalReference": asaas_sandbox_customer_external_reference(owner),
            "deleted": False,
        },
    )


def _listed_payment(user_id: int, reference: str, **overrides) -> dict:
    item = {
        "id": PAYMENT_ID,
        "customer": _customer_id(user_id),
        "value": float(PREPARED_VALUE),
        "billingType": "PIX",
        "externalReference": reference,
        "dueDate": DUE_DATE,
        "description": DESCRIPTION,
        "deleted": False,
    }
    item.update(overrides)
    return item


def _page(*items) -> tuple:
    return (200, {"data": list(items), "totalCount": len(items), "hasMore": False})


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def customer(db_session):
    user = User(email="asaas-sandbox-charge@test.local", hashed_password="x", role="customer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _created_payment(request, **overrides):
    """POST /payments 2xx: o Asaas ecoa os campos enviados + id/status."""
    body = {**request.json, "id": PAYMENT_ID, "status": "PENDING", "deleted": False}
    body.update(overrides)
    return 200, body


class FakeAsaas:
    """Fake do transporte: registra chamadas e devolve respostas roteirizadas."""

    def __init__(self, *, post=None, get=None, customer=None, listing=None):
        self.post_calls = []
        self.get_calls = []
        self.customer_calls = []
        self.list_calls = []
        self.customer_response = customer or _owned_customer
        self.list_response = listing or _page()
        self.post_response = post or _created_payment
        self.get_response = get or (
            200,
            {
                "success": True,
                "encodedImage": QR_IMAGE,
                "payload": QR_PAYLOAD,
                "expirationDate": QR_EXPIRATION,
            },
        )

    def _answer(self, response, request):
        if isinstance(response, BaseException):
            raise response
        if callable(response):
            return response(request)
        return response

    def http_post(self, request):
        self.post_calls.append(request)
        return self._answer(self.post_response, request)

    def http_get(self, request):
        # get_calls continua contando só o GET do QR Code.
        if request.operation == "get_customer":
            self.customer_calls.append(request)
            return self._answer(self.customer_response, request)
        if request.operation == "list_payments_by_external_reference":
            self.list_calls.append(request)
            return self._answer(self.list_response, request)
        self.get_calls.append(request)
        return self._answer(self.get_response, request)


def _charge(db, user_id, fake, *, reference, value=Decimal(PREPARED_VALUE), customer_id=None):
    return create_asaas_correlated_pix_charge(
        db,
        client=AsaasSandboxClient(TEST_CONFIG),
        user_id=user_id,
        customer_id=_customer_id(user_id) if customer_id is None else customer_id,
        value=value,
        due_date=DUE_DATE,
        description=DESCRIPTION,
        external_reference=reference,
        http_post=fake.http_post,
        http_get=fake.http_get,
    )


def _stored(db, reference) -> dict:
    db.expire_all()
    row = (
        db.query(IdempotencyKey)
        .filter_by(key=asaas_payment_correlation_key(reference))
        .one()
    )
    return json.loads(row.response_json)


def _assert_no_secret(value):
    text = repr(value) + str(value)
    assert API_KEY not in text
    assert PAYMENT_ID not in text


# --- service: sucesso -----------------------------------------------------


def test_success_posts_once_persists_payment_id_and_returns_qr(db_session, customer):
    fake = FakeAsaas()
    reference = _new_reference()

    result = _charge(db_session, customer.id, fake, reference=reference)

    assert len(fake.post_calls) == 1
    post = fake.post_calls[0]
    assert post.method == "POST"
    assert post.url == f"{ASAAS_SANDBOX_BASE_URL}/payments"
    assert post.json["billingType"] == "PIX"
    assert post.json["externalReference"] == reference
    assert post.json["value"] == 49.9

    assert len(fake.get_calls) == 1
    get = fake.get_calls[0]
    assert get.method == "GET"
    assert get.url == f"{ASAAS_SANDBOX_BASE_URL}/payments/{PAYMENT_ID}/pixQrCode"

    assert result.charge_replayed is False
    assert result.pix_qr_code == {
        "payload": QR_PAYLOAD,
        "encoded_image": QR_IMAGE,
        "expiration_date": QR_EXPIRATION,
    }

    stored = _stored(db_session, reference)
    assert stored["asaas_payment_id"] == PAYMENT_ID
    assert stored["charge_http_state"] == "created"
    assert stored["http_call_executed"] is True
    assert stored["real_money_enabled"] is False


def test_success_keeps_p03_credit_correlation_contract(db_session, customer):
    reference = _new_reference()

    _charge(db_session, customer.id, FakeAsaas(), reference=reference)

    correlation = resolve_asaas_payment_user_correlation(
        db_session, external_reference=reference
    )
    assert correlation is not None
    assert correlation.user_id == customer.id
    assert correlation.prepared_amount == Decimal(PREPARED_VALUE)


def test_result_repr_and_summary_never_expose_secret_or_payment_id(db_session, customer):
    result = _charge(db_session, customer.id, FakeAsaas(), reference=_new_reference())

    _assert_no_secret(result)
    _assert_no_secret(result.safe_summary())
    assert result.safe_summary()["http_call_executed"] is True
    assert result.safe_summary()["real_money"] is False


# --- service: replay ------------------------------------------------------


def test_replay_of_created_charge_never_posts_again(db_session, customer):
    fake = FakeAsaas()
    reference = _new_reference()

    _charge(db_session, customer.id, fake, reference=reference)
    replay = _charge(db_session, customer.id, fake, reference=reference)

    assert len(fake.post_calls) == 1
    assert len(fake.get_calls) == 2
    assert fake.get_calls[1].url.endswith(f"/payments/{PAYMENT_ID}/pixQrCode")
    assert replay.charge_replayed is True
    assert replay.pix_qr_code["payload"] == QR_PAYLOAD


def test_same_reference_with_different_data_is_conflict_without_post(db_session, customer):
    fake = FakeAsaas()
    reference = _new_reference()

    _charge(db_session, customer.id, fake, reference=reference)
    with pytest.raises(AsaasCorrelatedPixPaymentConflictError):
        _charge(db_session, customer.id, fake, reference=reference, value=Decimal("10.00"))

    assert len(fake.post_calls) == 1


def test_already_attempted_charge_only_reconciles_and_never_reposts(db_session, customer):
    reference = _new_reference()
    timeout = FakeAsaas(post=AsaasSandboxTransportError("timeout"))
    with pytest.raises(AsaasCorrelatedPixChargeProviderUnavailableError):
        _charge(db_session, customer.id, timeout, reference=reference)

    fake = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert fake.post_calls == []
    assert fake.customer_calls == []
    assert len(fake.list_calls) == 1
    assert fake.get_calls == []
    assert _stored(db_session, reference)["charge_http_state"] == "attempted"


# --- service: falhas no POST ----------------------------------------------


def test_post_timeout_fails_closed_and_keeps_attempted_state(db_session, customer):
    fake = FakeAsaas(post=AsaasSandboxTransportError("timeout"))
    reference = _new_reference()

    with pytest.raises(AsaasCorrelatedPixChargeProviderUnavailableError) as exc_info:
        _charge(db_session, customer.id, fake, reference=reference)

    _assert_no_secret(exc_info.value)
    assert len(fake.post_calls) == 1
    assert fake.get_calls == []
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "attempted"
    assert "asaas_payment_id" not in stored


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422, 429])
def test_post_4xx_fails_closed_marks_rejected_and_never_reposts(db_session, customer, status):
    fake = FakeAsaas(post=(status, {"errors": [{"code": "invalid", "description": API_KEY}]}))
    reference = _new_reference()

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError) as exc_info:
        _charge(db_session, customer.id, fake, reference=reference)

    _assert_no_secret(exc_info.value)
    assert fake.get_calls == []
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "rejected"
    assert "asaas_payment_id" not in stored

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert len(fake.post_calls) == 1


def _rejected_with(db, user_id, body, status=400) -> dict:
    fake = FakeAsaas(post=(status, body))
    reference = _new_reference()
    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError) as exc_info:
        _charge(db, user_id, fake, reference=reference)
    assert str(exc_info.value) == "Asaas Sandbox recusou a criação da cobrança."
    assert len(fake.post_calls) == 1
    return _stored(db, reference)


@pytest.mark.parametrize("status", [400, 404, 422])
def test_post_4xx_keeps_only_http_status_and_safe_error_codes(db_session, customer, status):
    body = {
        "errors": [
            {"code": "invalid_dueDate", "description": f"Data inválida {API_KEY}"},
            {"code": "invalid_value", "description": "joao@exemplo.com 123.456.789-00"},
        ],
        "headers": {"access_token": API_KEY},
    }

    stored = _rejected_with(db_session, customer.id, body, status=status)

    assert stored["charge_http_state"] == "rejected"
    assert stored["charge_http_status"] == status
    assert stored["charge_provider_error_codes"] == ["invalid_dueDate", "invalid_value"]
    raw = json.dumps(stored)
    assert API_KEY not in raw
    assert "description" not in raw
    assert "Data inválida" not in raw
    assert "joao@exemplo.com" not in raw
    assert "123.456.789-00" not in raw
    assert "headers" not in raw


@pytest.mark.parametrize(
    "code",
    [
        # Formato de código válido, mas carregando dado pessoal.
        "x12345678900",
        "cpf12345678900",
        "invalid_dueDate12345678900",
        "joao_silva",
        "joao_silva_exemplo_com",
        "invalid_email_joao",
        # Códigos plausíveis, mas não comprovados na documentação oficial.
        "invalid_customer",
        "invalid_billingType",
        "invalid_object",
        "internal_error",
        # Variações de códigos conhecidos.
        "INVALID_VALUE",
        "invalid_duedate",
        " invalid_value",
        "invalid_dueDate\n",
        # Formatos claramente inseguros ou inválidos.
        "joao@exemplo.com",
        "123.456.789-00",
        "12345678900",
        "",
        None,
        42,
        ["invalid_value"],
        {"code": "invalid_value"},
    ],
)
def test_post_4xx_discards_unknown_error_codes(db_session, customer, code):
    stored = _rejected_with(
        db_session, customer.id, {"errors": [{"code": code}, {"code": "invalid_value"}]}
    )

    assert stored["charge_provider_error_codes"] == ["invalid_value"]
    if isinstance(code, str) and code:
        assert code not in json.dumps(stored)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"errors": []},
        {"errors": None},
        {"errors": "invalid_value"},
        {"errors": {"code": "invalid_value"}},
        {"errors": ["invalid_value", 1, None]},
        {"errors": [{"code": "x12345678900"}, {"code": "joao_silva"}]},
        {"code": "invalid_value"},
        [],
        None,
        "invalid_value",
    ],
)
def test_post_4xx_without_known_errors_stores_empty_codes(db_session, customer, body):
    stored = _rejected_with(db_session, customer.id, body)

    assert stored["charge_http_status"] == 400
    assert stored["charge_provider_error_codes"] == []


def test_post_4xx_error_codes_are_deduplicated(db_session, customer):
    errors = [
        {"code": "invalid_value"},
        {"code": "invalid_dueDate"},
        {"code": "invalid_value"},
        {"code": "invalid_dueDate"},
    ]

    stored = _rejected_with(db_session, customer.id, {"errors": errors})

    assert stored["charge_provider_error_codes"] == ["invalid_value", "invalid_dueDate"]


def test_post_4xx_scans_only_first_error_items(db_session, customer):
    limit = charge_service._ASAAS_ERROR_ITEMS_SCANNED_MAX
    errors = [{"code": "unknown"}] * (limit - 1) + [
        {"code": "invalid_value"},
        {"code": "invalid_dueDate"},
    ]

    stored = _rejected_with(db_session, customer.id, {"errors": errors})

    assert stored["charge_provider_error_codes"] == ["invalid_value"]


def test_post_4xx_huge_error_list_is_bounded(db_session, customer):
    errors = [{"code": "x12345678900"}] * 100_000 + [{"code": "invalid_value"}]

    stored = _rejected_with(db_session, customer.id, {"errors": errors})

    assert stored["charge_provider_error_codes"] == []


def test_post_4xx_diagnostic_does_not_change_replay_or_lock(db_session, customer):
    reference = _new_reference()
    fake = FakeAsaas(post=(400, {"errors": [{"code": "invalid_dueDate"}]}))
    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert len(fake.post_calls) == 1
    assert fake.list_calls == []
    assert _stored(db_session, reference)["charge_provider_error_codes"] == ["invalid_dueDate"]

    # Lock liberado: outra referência do mesmo usuário pode cobrar.
    ok = FakeAsaas()
    _charge(db_session, customer.id, ok, reference=_new_reference())
    assert len(ok.post_calls) == 1


def test_post_4xx_diagnostic_cas_failure_stays_attempted_without_codes(db_session, customer, monkeypatch):
    def lose_cas(db, **kwargs):
        if kwargs["contract"].get("charge_http_state") == "rejected":
            return False, None
        return original(db, **kwargs)

    original = charge_service._compare_and_set_contract
    monkeypatch.setattr(charge_service, "_compare_and_set_contract", lose_cas)
    reference = _new_reference()
    fake = FakeAsaas(post=(400, {"errors": [{"code": "invalid_dueDate"}]}))

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)

    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "attempted"
    assert "charge_http_status" not in stored
    assert "charge_provider_error_codes" not in stored


@pytest.mark.parametrize("status", [500, 503])
def test_post_5xx_does_not_store_error_diagnostic(db_session, customer, status):
    fake = FakeAsaas(post=(status, {"errors": [{"code": "internal_error"}]}))
    reference = _new_reference()

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)

    stored = _stored(db_session, reference)
    assert "charge_http_status" not in stored
    assert "charge_provider_error_codes" not in stored


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_post_5xx_fails_closed_and_stays_indeterminate(db_session, customer, status):
    fake = FakeAsaas(post=(status, {}))
    reference = _new_reference()

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert _stored(db_session, reference)["charge_http_state"] == "attempted"
    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert len(fake.post_calls) == 1
    assert len(fake.list_calls) == 1


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"id": ""},
        {"id": 123},
        {"id": "pay_../../x"},
        {"id": "pay_" + "a" * 80},
        {"id": PAYMENT_ID, "externalReference": "agpay_" + "f" * 32},
    ],
)
def test_post_2xx_with_invalid_body_fails_closed(db_session, customer, body):
    fake = FakeAsaas(post=(200, body))
    reference = _new_reference()

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert fake.get_calls == []
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "attempted"
    assert "asaas_payment_id" not in stored


# P1-A: a resposta 2xx do POST passa pelo mesmo critério da reconciliação.
@pytest.mark.parametrize(
    "overrides",
    [
        {"externalReference": None},
        {"externalReference": "agpay_" + "f" * 32},
        {"customer": "cus_someoneelse"},
        {"customer": None},
        {"value": 10.0},
        {"value": True},
        {"value": None},
        {"billingType": "BOLETO"},
        {"billingType": None},
        {"dueDate": "2027-01-01"},
        {"description": "outra"},
        {"deleted": True},
    ],
)
def test_post_2xx_divergent_from_preparation_fails_closed(db_session, customer, overrides):
    fake = FakeAsaas(post=lambda request: _created_payment(request, **overrides))
    reference = _new_reference()

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert fake.get_calls == []
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "attempted"
    assert "asaas_payment_id" not in stored


# --- service: janela POST aceito -> falha de persistência ------------------


def test_payment_id_persist_failure_blocks_second_post(db_session, customer, monkeypatch):
    fake = FakeAsaas()
    reference = _new_reference()
    real_commit = db_session.commit

    def failing_commit_after_post():
        if fake.post_calls:
            raise OperationalError("commit", {}, Exception("simulated"))
        return real_commit()

    monkeypatch.setattr(db_session, "commit", failing_commit_after_post)
    with pytest.raises(AsaasCorrelatedPixPaymentStorageError):
        _charge(db_session, customer.id, fake, reference=reference)
    monkeypatch.setattr(db_session, "commit", real_commit)

    assert len(fake.post_calls) == 1
    assert fake.get_calls == []
    assert _stored(db_session, reference)["charge_http_state"] == "attempted"

    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert len(fake.post_calls) == 1
    assert len(fake.list_calls) == 1


def test_attempted_state_persist_failure_never_posts(db_session, customer, monkeypatch):
    fake = FakeAsaas()
    reference = _new_reference()
    real_commit = db_session.commit
    commits = itertools.count()

    def fail_second_commit():
        # 1º commit: preparação local; 2º: estado "attempted".
        if next(commits) == 1:
            raise OperationalError("commit", {}, Exception("simulated"))
        return real_commit()

    monkeypatch.setattr(db_session, "commit", fail_second_commit)
    with pytest.raises(AsaasCorrelatedPixPaymentStorageError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert fake.post_calls == []
    assert "charge_http_state" not in _stored(db_session, reference)


# --- service: falhas no GET QR --------------------------------------------


def test_get_qr_timeout_fails_closed_keeps_payment_id_and_replay_does_not_repost(db_session, customer):
    fake = FakeAsaas(get=AsaasSandboxTransportError("timeout"))
    reference = _new_reference()

    with pytest.raises(AsaasCorrelatedPixChargeProviderUnavailableError):
        _charge(db_session, customer.id, fake, reference=reference)

    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "created"
    assert stored["asaas_payment_id"] == PAYMENT_ID

    recovered = FakeAsaas()
    replay = _charge(db_session, customer.id, recovered, reference=reference)

    assert recovered.post_calls == []
    assert len(recovered.get_calls) == 1
    assert replay.pix_qr_code["payload"] == QR_PAYLOAD


@pytest.mark.parametrize(
    "response",
    [
        (404, {}),
        (500, {}),
        (200, {}),
        (200, {"payload": "", "encodedImage": QR_IMAGE, "expirationDate": QR_EXPIRATION}),
        (200, {"payload": QR_PAYLOAD, "encodedImage": None, "expirationDate": QR_EXPIRATION}),
        (200, {"payload": QR_PAYLOAD, "encodedImage": QR_IMAGE}),
    ],
)
def test_get_qr_error_or_invalid_body_fails_closed(db_session, customer, response):
    fake = FakeAsaas(get=response)

    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=_new_reference())

    assert len(fake.post_calls) == 1


def test_qr_result_contains_only_qr_fields(db_session, customer):
    fake = FakeAsaas(
        get=(
            200,
            {
                "encodedImage": QR_IMAGE,
                "payload": QR_PAYLOAD,
                "expirationDate": QR_EXPIRATION,
                "extra": API_KEY,
            },
        )
    )

    result = _charge(db_session, customer.id, fake, reference=_new_reference())

    assert set(result.pix_qr_code) == {"payload", "encoded_image", "expiration_date"}
    _assert_no_secret(result.pix_qr_code)


# --- transporte httpx -----------------------------------------------------


def _transport(handler, config=TEST_CONFIG):
    return AsaasSandboxHttpTransport(config, transport=httpx.MockTransport(handler))


def _client(config=TEST_CONFIG):
    return AsaasSandboxClient(config)


def test_transport_default_timeout_is_10_seconds():
    assert ASAAS_SANDBOX_HTTP_TIMEOUT_SECONDS == 10.0
    assert AsaasSandboxHttpTransport(TEST_CONFIG).timeout == 10.0


def test_transport_post_sends_api_key_header_and_json_once():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"id": PAYMENT_ID})

    prepared = _client().prepare_create_pix_payment(
        customer_id="cus_1",
        value=Decimal("1.00"),
        due_date="2026-12-31",
        description="d",
        external_reference="agpay_" + "a" * 32,
    )
    status, body = _transport(handler).post(prepared)

    assert (status, body) == (200, {"id": PAYMENT_ID})
    assert len(seen) == 1
    request = seen[0]
    assert request.method == "POST"
    assert str(request.url) == f"{ASAAS_SANDBOX_BASE_URL}/payments"
    assert request.headers["access_token"] == API_KEY
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content)["billingType"] == "PIX"
    assert request.extensions["timeout"]["read"] == 10.0


def test_transport_get_qr_code():
    def handler(request):
        assert request.method == "GET"
        assert str(request.url) == f"{ASAAS_SANDBOX_BASE_URL}/payments/{PAYMENT_ID}/pixQrCode"
        return httpx.Response(200, json={"payload": QR_PAYLOAD})

    status, body = _transport(handler).get(_client().prepare_get_pix_qr_code(payment_id=PAYMENT_ID))

    assert (status, body) == (200, {"payload": QR_PAYLOAD})


def test_transport_non_json_or_non_object_body_becomes_empty_dict():
    def handler(request):
        return httpx.Response(502, content=b"<html>bad gateway</html>")

    status, body = _transport(handler).get(_client().prepare_get_pix_qr_code(payment_id=PAYMENT_ID))
    assert (status, body) == (502, {})

    status, body = _transport(lambda r: httpx.Response(200, json=[1, 2])).get(
        _client().prepare_get_pix_qr_code(payment_id=PAYMENT_ID)
    )
    assert (status, body) == (200, {})


def test_transport_timeout_is_sanitized_and_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout(f"timeout with {API_KEY}", request=request)

    with pytest.raises(AsaasSandboxTransportError) as exc_info:
        _transport(handler).post(
            _client().prepare_create_pix_payment(
                customer_id="cus_1",
                value=Decimal("1.00"),
                due_date="2026-12-31",
                description="d",
            )
        )

    assert len(calls) == 1
    assert API_KEY not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_transport_does_not_follow_redirects():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={"location": "https://evil.example/payments"})

    status, _ = _transport(handler).get(_client().prepare_get_pix_qr_code(payment_id=PAYMENT_ID))

    assert status == 302
    assert len(calls) == 1


@pytest.mark.parametrize(
    "config",
    [
        AsaasSandboxConfig(
            env="production",
            base_url=ASAAS_SANDBOX_BASE_URL,
            api_key=API_KEY,
            webhook_token="t",
            real_money_enabled=False,
            wallet_mode="partner",
            wallet_partner_provider="asaas",
        ),
        AsaasSandboxConfig(
            env="sandbox",
            base_url=ASAAS_PRODUCTION_BASE_URL,
            api_key=API_KEY,
            webhook_token="t",
            real_money_enabled=False,
            wallet_mode="partner",
            wallet_partner_provider="asaas",
        ),
        AsaasSandboxConfig(
            env="sandbox",
            base_url=ASAAS_SANDBOX_BASE_URL,
            api_key=API_KEY,
            webhook_token="t",
            real_money_enabled=True,
            wallet_mode="partner",
            wallet_partner_provider="asaas",
        ),
        AsaasSandboxConfig(
            env="sandbox",
            base_url=ASAAS_SANDBOX_BASE_URL,
            api_key="",
            webhook_token="t",
            real_money_enabled=False,
            wallet_mode="partner",
            wallet_partner_provider="asaas",
        ),
    ],
)
def test_transport_refuses_non_sandbox_config(config):
    with pytest.raises(AsaasSandboxTransportError) as exc_info:
        AsaasSandboxHttpTransport(config)
    assert API_KEY not in str(exc_info.value)


def test_transport_refuses_url_outside_sandbox_and_wrong_method():
    calls = []
    transport = _transport(lambda r: calls.append(r) or httpx.Response(200, json={}))
    get_request = _client().prepare_get_pix_qr_code(payment_id=PAYMENT_ID)
    foreign = SimpleNamespace(
        method="GET", url=f"{ASAAS_PRODUCTION_BASE_URL}/payments/x/pixQrCode", json=None
    )
    lookalike = SimpleNamespace(
        method="GET", url=f"{ASAAS_SANDBOX_BASE_URL}.evil.example/payments", json=None
    )

    for request in (foreign, lookalike):
        with pytest.raises(AsaasSandboxTransportError):
            transport.get(request)
    with pytest.raises(AsaasSandboxTransportError):
        transport.post(get_request)

    assert calls == []


def test_transport_repr_masks_api_key():
    assert API_KEY not in repr(AsaasSandboxHttpTransport(TEST_CONFIG))


# --- endpoint -------------------------------------------------------------


@pytest.fixture()
def endpoint(monkeypatch):
    limiter.reset()
    monkeypatch.setattr(wallet_routes, "load_asaas_sandbox_config", lambda: TEST_CONFIG)
    monkeypatch.delenv("ASAAS_SANDBOX_CHARGE_HTTP_ENABLED", raising=False)
    fake = FakeAsaas()
    built = []

    def build(config):
        built.append(config)
        return SimpleNamespace(post=fake.http_post, get=fake.http_get)

    monkeypatch.setattr(wallet_routes, "_build_asaas_sandbox_charge_transport", build)
    yield SimpleNamespace(fake=fake, built=built)
    limiter.reset()


@pytest.fixture()
def charge_on(monkeypatch):
    monkeypatch.setenv("ASAAS_SANDBOX_CHARGE_HTTP_ENABLED", "true")


def _request() -> StarletteRequest:
    host = f"203.0.113.{next(_hosts) % 250 + 1}"
    path = "/api/v1/wallet/pix/asaas/sandbox/prepare"
    return StarletteRequest(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "raw_path": path.encode("utf-8"),
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": (host, 12345),
            "scheme": "http",
            "app": None,
        }
    )


def _call(db, user, *, amount=PREPARED_VALUE, customer_id=None, **kwargs):
    return wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
        request=_request(),
        payload=wallet_routes.WalletAsaasCorrelatedPixPaymentPreparationIn(
            customer_id=_customer_id(user.id) if customer_id is None else customer_id,
            amount=Decimal(amount),
            due_date=DUE_DATE,
        ),
        current_user=SimpleNamespace(id=user.id),
        db=db,
        **kwargs,
    )


@pytest.mark.parametrize("value", [None, "", "false", "1", "yes", "truee"])
def test_endpoint_flag_off_never_calls_http(db_session, customer, endpoint, monkeypatch, value):
    if value is not None:
        monkeypatch.setenv("ASAAS_SANDBOX_CHARGE_HTTP_ENABLED", value)

    response = _call(db_session, customer, idempotency_key="charge-key-0001")

    assert endpoint.built == []
    assert endpoint.fake.post_calls == []
    assert endpoint.fake.get_calls == []
    assert response["operation"] == "prepare_asaas_correlated_pix_payment"
    assert response["can_send_http"] is False
    assert response["can_create_charge"] is False
    assert "pix_qr_code" not in response


def test_endpoint_flag_on_creates_charge_and_returns_only_qr(db_session, customer, endpoint, charge_on):
    response = _call(db_session, customer, idempotency_key="charge-key-0001")

    assert endpoint.built == [TEST_CONFIG]
    assert len(endpoint.fake.post_calls) == 1
    assert response["ok"] is True
    assert response["operation"] == "create_asaas_correlated_pix_charge"
    assert response["pix_qr_code"] == {
        "payload": QR_PAYLOAD,
        "encoded_image": QR_IMAGE,
        "expiration_date": QR_EXPIRATION,
    }
    assert response["can_create_charge"] is True
    assert response["can_credit_balance"] is False
    assert response["wallet"]["real_money_enabled"] is False
    serialized = json.dumps(response)
    assert API_KEY not in serialized
    assert PAYMENT_ID not in serialized
    assert "agpay_" not in serialized
    assert _customer_id(customer.id) not in serialized


def test_endpoint_flag_on_replay_same_key_does_not_post_again(db_session, customer, endpoint, charge_on):
    first = _call(db_session, customer, idempotency_key="charge-key-0001")
    second = _call(db_session, customer, idempotency_key="charge-key-0001")

    assert len(endpoint.fake.post_calls) == 1
    assert first["charge"]["charge_replayed"] is False
    assert second["charge"]["charge_replayed"] is True
    assert second["pix_qr_code"] == first["pix_qr_code"]


def test_endpoint_flag_on_different_keys_create_distinct_charges(db_session, customer, endpoint, charge_on):
    _call(db_session, customer, idempotency_key="charge-key-0001")
    _call(db_session, customer, idempotency_key="charge-key-0002")

    references = {call.json["externalReference"] for call in endpoint.fake.post_calls}
    assert len(references) == 2


def test_endpoint_flag_on_same_key_other_user_never_shares_charge(db_session, customer, endpoint, charge_on):
    other = User(email="asaas-sandbox-charge-2@test.local", hashed_password="x", role="customer")
    db_session.add(other)
    db_session.commit()

    _call(db_session, customer, idempotency_key="charge-key-0001")
    _call(db_session, other, idempotency_key="charge-key-0001")

    assert len(endpoint.fake.post_calls) == 2
    first, second = (call.json["externalReference"] for call in endpoint.fake.post_calls)
    assert first != second


def test_endpoint_flag_on_same_key_different_amount_is_409(db_session, customer, endpoint, charge_on):
    _call(db_session, customer, idempotency_key="charge-key-0001")

    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key="charge-key-0001", amount="10.00")

    assert exc_info.value.status_code == 409
    assert len(endpoint.fake.post_calls) == 1


@pytest.mark.parametrize("key", [None, ""])
def test_endpoint_flag_on_requires_idempotency_key(db_session, customer, endpoint, charge_on, key):
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key=key)

    assert exc_info.value.status_code == 400
    assert endpoint.fake.post_calls == []


@pytest.mark.parametrize("key", ["short", "x" * 129, "bad key with spaces", "chave/ç"])
def test_endpoint_flag_on_rejects_invalid_idempotency_key(db_session, customer, endpoint, charge_on, key):
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key=key)

    assert exc_info.value.status_code == 422
    assert endpoint.fake.post_calls == []


@pytest.mark.parametrize(
    "post, get, status",
    [
        (AsaasSandboxTransportError("timeout"), None, 503),
        ((400, {"errors": [{"description": API_KEY}]}), None, 502),
        ((500, {}), None, 502),
        (None, AsaasSandboxTransportError("timeout"), 503),
        (None, (500, {}), 502),
    ],
)
def test_endpoint_flag_on_provider_failures_fail_closed(
    db_session, customer, endpoint, charge_on, post, get, status
):
    if post is not None:
        endpoint.fake.post_response = post
    if get is not None:
        endpoint.fake.get_response = get

    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key="charge-key-0001")

    assert exc_info.value.status_code == status
    assert API_KEY not in str(exc_info.value.detail)
    assert PAYMENT_ID not in str(exc_info.value.detail)


def test_endpoint_flag_on_4xx_detail_stays_generic_without_error_codes(
    db_session, customer, endpoint, charge_on
):
    endpoint.fake.post_response = (
        400,
        {"errors": [{"code": "invalid_dueDate", "description": "Data de vencimento inválida"}]},
    )

    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key="charge-key-0001")

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Asaas Sandbox recusou ou falhou ao processar a cobrança PIX."
    assert "invalid_dueDate" not in str(exc_info.value.detail)
    assert "400" not in str(exc_info.value.detail)


def test_endpoint_flag_on_indeterminate_replay_is_409_without_post(db_session, customer, endpoint, charge_on):
    endpoint.fake.post_response = AsaasSandboxTransportError("timeout")
    with pytest.raises(HTTPException):
        _call(db_session, customer, idempotency_key="charge-key-0001")

    endpoint.fake.post_response = (200, {"id": PAYMENT_ID})
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key="charge-key-0001")

    assert exc_info.value.status_code == 409
    assert len(endpoint.fake.post_calls) == 1
    assert len(endpoint.fake.list_calls) == 1


def test_endpoint_flag_on_transport_build_failure_is_503(db_session, customer, endpoint, charge_on, monkeypatch):
    def refuse(config):
        raise AsaasSandboxTransportError("refused")

    monkeypatch.setattr(wallet_routes, "_build_asaas_sandbox_charge_transport", refuse)

    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key="charge-key-0001")

    assert exc_info.value.status_code == 503
    assert db_session.query(IdempotencyKey).count() == 0


def test_default_transport_factory_builds_real_sandbox_transport():
    transport = wallet_routes._build_asaas_sandbox_charge_transport(TEST_CONFIG)

    assert isinstance(transport, AsaasSandboxHttpTransport)
    assert transport.timeout == 10.0


# --- P0: lock por usuário, reconciliação e transições via CAS --------------


@pytest.fixture()
def other_customer(db_session):
    user = User(email="asaas-sandbox-charge-other@test.local", hashed_password="x", role="customer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _correlation_contract(db, reference):
    db.expire_all()
    row = (
        db.query(IdempotencyKey)
        .filter_by(key=asaas_payment_correlation_key(reference))
        .one_or_none()
    )
    return None if row is None else json.loads(row.response_json)


def _lock_row(db, user_id):
    db.expire_all()
    return (
        db.query(IdempotencyKey)
        .filter_by(key=charge_service._pending_lock_key(user_id))
        .one_or_none()
    )


def _age_attempt(db, reference, minutes=11):
    row = (
        db.query(IdempotencyKey)
        .filter_by(key=asaas_payment_correlation_key(reference))
        .one()
    )
    contract = json.loads(row.response_json)
    contract["charge_attempted_at"] = (
        datetime.now(timezone.utc) - timedelta(minutes=minutes)
    ).isoformat()
    row.response_json = json.dumps(contract)
    db.commit()


def _attempt_with_timeout(db, user_id, reference):
    fake = FakeAsaas(post=AsaasSandboxTransportError("timeout"))
    with pytest.raises(AsaasCorrelatedPixChargeProviderUnavailableError):
        _charge(db, user_id, fake, reference=reference)
    assert len(fake.post_calls) == 1
    assert _stored(db, reference)["charge_http_state"] == "attempted"


def _no_http(fake):
    return (
        fake.post_calls == []
        and fake.get_calls == []
        and fake.customer_calls == []
        and fake.list_calls == []
    )


def _webhook(db, reference, user_id, payment_id=PAYMENT_ID):
    result = apply_asaas_webhook_charge_transition(
        db,
        correlation_key=asaas_payment_correlation_key(reference),
        user_id=user_id,
        payment_id=payment_id,
    )
    db.commit()
    return result


def test_t1_pending_charge_blocks_new_key_without_customer_get_or_post(db_session, customer):
    first = _new_reference()
    _attempt_with_timeout(db_session, customer.id, first)
    assert _lock_row(db_session, customer.id) is not None

    fake = FakeAsaas()
    second = _new_reference()
    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, fake, reference=second)

    assert _no_http(fake)
    assert "charge_http_state" not in _correlation_contract(db_session, second)


def test_t1_lock_is_per_user(db_session, customer, other_customer):
    _attempt_with_timeout(db_session, customer.id, _new_reference())

    fake = FakeAsaas()
    _charge(db_session, other_customer.id, fake, reference=_new_reference())
    assert len(fake.post_calls) == 1


def test_t2_lock_released_after_created(db_session, customer):
    fake = FakeAsaas()
    _charge(db_session, customer.id, fake, reference=_new_reference())
    assert _lock_row(db_session, customer.id) is None

    _charge(db_session, customer.id, fake, reference=_new_reference())
    assert len(fake.post_calls) == 2


def test_t3_lock_released_after_rejected(db_session, customer):
    rejected = FakeAsaas(post=(400, {"errors": []}))
    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, rejected, reference=_new_reference())
    assert _lock_row(db_session, customer.id) is None

    fake = FakeAsaas()
    _charge(db_session, customer.id, fake, reference=_new_reference())
    assert len(rejected.post_calls) == 1
    assert len(fake.post_calls) == 1


def test_t4_reconcile_single_matching_payment_marks_created_without_post(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)

    fake = FakeAsaas(listing=_page(_listed_payment(customer.id, reference)))
    result = _charge(db_session, customer.id, fake, reference=reference)

    assert fake.post_calls == []
    assert fake.customer_calls == []
    assert len(fake.list_calls) == 1
    assert "externalReference=" in fake.list_calls[0].url
    assert len(fake.get_calls) == 1
    assert result.pix_qr_code["payload"] == QR_PAYLOAD
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "created"
    assert stored["asaas_payment_id"] == PAYMENT_ID
    assert _lock_row(db_session, customer.id) is None

    replay = FakeAsaas()
    again = _charge(db_session, customer.id, replay, reference=reference)
    assert again.charge_replayed is True
    assert replay.post_calls == [] and replay.list_calls == []
    assert len(replay.get_calls) == 1


def test_t5_reconcile_empty_list_inside_window_stays_pending(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)
    before = _stored(db_session, reference)

    fake = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert fake.post_calls == [] and fake.get_calls == []
    assert len(fake.list_calls) == 1
    assert _stored(db_session, reference) == before
    assert _lock_row(db_session, customer.id) is not None


def test_t6_reconcile_empty_list_after_window_is_not_created(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)
    _age_attempt(db_session, reference)

    fake = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert fake.post_calls == [] and len(fake.list_calls) == 1
    assert _stored(db_session, reference)["charge_http_state"] == "not_created"
    assert _lock_row(db_session, customer.id) is None

    retry = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, retry, reference=reference)
    assert _no_http(retry)

    fresh = FakeAsaas()
    _charge(db_session, customer.id, fresh, reference=_new_reference())
    assert len(fresh.post_calls) == 1


def test_t6_legacy_attempt_without_timestamp_never_becomes_not_created(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)
    row = (
        db_session.query(IdempotencyKey)
        .filter_by(key=asaas_payment_correlation_key(reference))
        .one()
    )
    contract = json.loads(row.response_json)
    contract.pop("charge_attempted_at")
    row.response_json = json.dumps(contract)
    db_session.commit()

    fake = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert fake.post_calls == []
    assert _stored(db_session, reference)["charge_http_state"] == "attempted"


def test_t7_reconcile_multiple_payments_is_conflict_and_keeps_lock(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)

    item = _listed_payment(customer.id, reference)
    fake = FakeAsaas(listing=_page(item, {**item, "id": "pay_other1"}))
    with pytest.raises(AsaasCorrelatedPixChargeConflictError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert fake.post_calls == [] and fake.get_calls == []
    assert _stored(db_session, reference)["charge_http_state"] == "conflict"
    assert _lock_row(db_session, customer.id) is not None

    retry = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargeConflictError):
        _charge(db_session, customer.id, retry, reference=reference)
    assert _no_http(retry)

    other_key = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, other_key, reference=_new_reference())
    assert _no_http(other_key)


@pytest.mark.parametrize(
    "overrides",
    [
        {"id": "pay_../x"},
        {"id": 123},
        {"billingType": "BOLETO"},
        {"externalReference": "agpay_" + "f" * 32},
        {"deleted": True},
        {"dueDate": "2027-01-01"},
        {"description": "outra"},
        {"value": 10.0},
        {"value": True},
        {"customer": "cus_someoneelse"},
        {"customer": None},
    ],
)
def test_t8_reconcile_divergent_payment_is_conflict_without_post(db_session, customer, overrides):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)

    fake = FakeAsaas(listing=_page(_listed_payment(customer.id, reference, **overrides)))
    with pytest.raises(AsaasCorrelatedPixChargeConflictError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert fake.post_calls == [] and fake.get_calls == []
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "conflict"
    assert "asaas_payment_id" not in stored


def test_t8_reconcile_list_with_has_more_is_conflict(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)

    listing = (
        200,
        {"data": [_listed_payment(customer.id, reference)], "totalCount": 2, "hasMore": True},
    )
    fake = FakeAsaas(listing=listing)
    with pytest.raises(AsaasCorrelatedPixChargeConflictError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert fake.post_calls == []


@pytest.mark.parametrize(
    "listing",
    [
        AsaasSandboxTransportError("timeout"),
        (500, {}),
        (404, {}),
        (200, {}),
        (200, {"data": "x"}),
        (200, []),
    ],
)
def test_t9_reconcile_list_failure_stays_pending_without_post(db_session, customer, listing):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)
    before = _stored(db_session, reference)

    fake = FakeAsaas(listing=listing)
    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert fake.post_calls == [] and fake.get_calls == []
    assert len(fake.list_calls) == 1
    assert _stored(db_session, reference) == before


def test_t10_reconcile_cas_loss_stays_pending_without_post(db_session, customer, monkeypatch):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)
    monkeypatch.setattr(
        charge_service, "_compare_and_set_contract", lambda db, **kwargs: (False, None)
    )

    fake = FakeAsaas(listing=_page(_listed_payment(customer.id, reference)))
    with pytest.raises(AsaasCorrelatedPixChargePendingError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert fake.post_calls == [] and fake.get_calls == []
    assert _stored(db_session, reference)["charge_http_state"] == "attempted"


def test_t10_claim_cas_loss_is_indeterminate_without_post(db_session, customer, monkeypatch):
    monkeypatch.setattr(
        charge_service, "_compare_and_set_contract", lambda db, **kwargs: (False, None)
    )
    fake = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargeIndeterminateError):
        _charge(db_session, customer.id, fake, reference=_new_reference())
    assert fake.post_calls == []


def test_t11_webhook_attempted_to_created_releases_lock_and_replay_only_gets_qr(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)

    assert _webhook(db_session, reference, customer.id) == "created"
    assert "created" in ASAAS_WEBHOOK_CHARGE_CREDITABLE_STATUSES
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "created"
    assert stored["asaas_payment_id"] == PAYMENT_ID
    assert _lock_row(db_session, customer.id) is None

    fake = FakeAsaas()
    replay = _charge(db_session, customer.id, fake, reference=reference)
    assert replay.charge_replayed is True
    assert fake.post_calls == [] and fake.list_calls == [] and fake.customer_calls == []
    assert len(fake.get_calls) == 1

    # Webhook repetido com o mesmo id é idempotente.
    assert _webhook(db_session, reference, customer.id) == "created"


def test_t12_webhook_not_created_to_created_late(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)
    _age_attempt(db_session, reference)
    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, FakeAsaas(), reference=reference)

    result = _webhook(db_session, reference, customer.id)
    assert result == "created_late"
    assert result in ASAAS_WEBHOOK_CHARGE_CREDITABLE_STATUSES
    assert _stored(db_session, reference)["charge_http_state"] == "created_late"

    fake = FakeAsaas()
    replay = _charge(db_session, customer.id, fake, reference=reference)
    assert replay.charge_replayed is True
    assert fake.post_calls == [] and len(fake.get_calls) == 1


def test_t13_webhook_divergent_payment_id_on_created_becomes_conflict(db_session, customer):
    reference = _new_reference()
    _charge(db_session, customer.id, FakeAsaas(), reference=reference)

    result = _webhook(db_session, reference, customer.id, payment_id="pay_divergent1")
    assert result == "payment_id_conflict"
    assert result not in ASAAS_WEBHOOK_CHARGE_CREDITABLE_STATUSES
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "conflict"
    assert stored["asaas_payment_id"] == PAYMENT_ID

    fake = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargeConflictError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert _no_http(fake)


def test_t13_webhook_divergent_payment_id_on_created_late_is_not_creditable(db_session, customer):
    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)
    _age_attempt(db_session, reference)
    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, FakeAsaas(), reference=reference)
    assert _webhook(db_session, reference, customer.id) == "created_late"

    result = _webhook(db_session, reference, customer.id, payment_id="pay_divergent1")
    assert result == "payment_id_conflict"
    stored = _stored(db_session, reference)
    assert stored["charge_http_state"] == "created_late"
    assert stored["asaas_payment_id"] == PAYMENT_ID


def test_t14_webhook_on_rejected_or_conflict_is_not_creditable(db_session, customer):
    rejected = _new_reference()
    with pytest.raises(AsaasCorrelatedPixChargeProviderRejectedError):
        _charge(db_session, customer.id, FakeAsaas(post=(400, {})), reference=rejected)
    assert _webhook(db_session, rejected, customer.id) == "conflict"
    assert _stored(db_session, rejected)["charge_http_state"] == "rejected"

    conflicted = _new_reference()
    _attempt_with_timeout(db_session, customer.id, conflicted)
    item = _listed_payment(customer.id, conflicted)
    with pytest.raises(AsaasCorrelatedPixChargeConflictError):
        _charge(
            db_session,
            customer.id,
            FakeAsaas(listing=_page(item, {**item, "id": "pay_other1"})),
            reference=conflicted,
        )
    assert _webhook(db_session, conflicted, customer.id) == "conflict"
    assert _stored(db_session, conflicted)["charge_http_state"] == "conflict"
    assert "conflict" not in ASAAS_WEBHOOK_CHARGE_CREDITABLE_STATUSES


def test_t14_webhook_invalid_payment_id_wrong_user_or_untracked(db_session, customer, other_customer):
    # Correlação preparada sem tentativa de cobrança: comportamento anterior.
    untracked = _new_reference()
    with pytest.raises(AsaasCorrelatedPixChargeCustomerMismatchError):
        _charge(
            db_session,
            customer.id,
            FakeAsaas(customer=(200, {"id": _customer_id(customer.id)})),
            reference=untracked,
        )
    assert _webhook(db_session, untracked, customer.id) == "untracked"
    assert "untracked" in ASAAS_WEBHOOK_CHARGE_CREDITABLE_STATUSES
    assert _webhook(db_session, _new_reference(), customer.id) == "invalid_state"

    reference = _new_reference()
    _attempt_with_timeout(db_session, customer.id, reference)

    assert _webhook(db_session, reference, customer.id, payment_id="pay_../x") == "invalid_state"
    assert _webhook(db_session, reference, customer.id, payment_id=None) == "invalid_state"
    assert _webhook(db_session, reference, other_customer.id) == "invalid_state"
    assert _stored(db_session, reference)["charge_http_state"] == "attempted"


# --- P1: ownership do customer via externalReference "agcus_" --------------


@pytest.mark.parametrize(
    "customer_id",
    ["cus_bad_format", "cus_", "pay_abc", "cus_abc/../x", "", "cus_" + "a" * 61],
)
def test_c1_invalid_customer_format_never_calls_http(db_session, customer, customer_id):
    fake = FakeAsaas()
    with pytest.raises(ValueError):
        _charge(db_session, customer.id, fake, reference=_new_reference(), customer_id=customer_id)
    assert _no_http(fake)


@pytest.mark.parametrize(
    "response",
    [
        AsaasSandboxTransportError("timeout"),
        (500, {}),
        (404, {}),
        (401, {}),
        (200, []),
    ],
)
def test_c2_customer_get_failure_is_unavailable_without_claim_or_post(db_session, customer, response):
    fake = FakeAsaas(customer=response)
    reference = _new_reference()
    with pytest.raises(AsaasCorrelatedPixChargeProviderUnavailableError):
        _charge(db_session, customer.id, fake, reference=reference)

    assert len(fake.customer_calls) == 1
    assert fake.post_calls == [] and fake.list_calls == [] and fake.get_calls == []
    assert "charge_http_state" not in _correlation_contract(db_session, reference)
    assert _lock_row(db_session, customer.id) is None


@pytest.mark.parametrize(
    "body",
    [
        {"deleted": False},
        {"externalReference": None},
        {"externalReference": "agcus_wrong"},
        {"externalReference": "other-system-ref"},
    ],
)
def test_c3_customer_without_matching_agcus_is_mismatch(db_session, customer, body):
    fake = FakeAsaas(customer=(200, {"id": _customer_id(customer.id), "deleted": False, **body}))
    reference = _new_reference()
    with pytest.raises(AsaasCorrelatedPixChargeCustomerMismatchError):
        _charge(db_session, customer.id, fake, reference=reference)
    assert fake.post_calls == []
    assert "charge_http_state" not in _correlation_contract(db_session, reference)


def test_c3_customer_of_another_user_is_never_accepted(db_session, customer, other_customer):
    # customer_id real do outro usuário: o agcus_ devolvido é do dono real.
    fake = FakeAsaas()
    with pytest.raises(AsaasCorrelatedPixChargeCustomerMismatchError):
        _charge(
            db_session,
            customer.id,
            fake,
            reference=_new_reference(),
            customer_id=_customer_id(other_customer.id),
        )
    assert len(fake.customer_calls) == 1
    assert fake.post_calls == []


def test_c4_deleted_customer_is_mismatch(db_session, customer):
    body = {
        "id": _customer_id(customer.id),
        "externalReference": asaas_sandbox_customer_external_reference(customer.id),
        "deleted": True,
    }
    fake = FakeAsaas(customer=(200, body))
    with pytest.raises(AsaasCorrelatedPixChargeCustomerMismatchError):
        _charge(db_session, customer.id, fake, reference=_new_reference())
    assert fake.post_calls == []


@pytest.mark.parametrize("returned_id", ["cus_different1", None, ""])
def test_c5_customer_id_divergence_is_mismatch(db_session, customer, returned_id):
    body = {
        "id": returned_id,
        "externalReference": asaas_sandbox_customer_external_reference(customer.id),
        "deleted": False,
    }
    fake = FakeAsaas(customer=(200, body))
    with pytest.raises(AsaasCorrelatedPixChargeCustomerMismatchError):
        _charge(db_session, customer.id, fake, reference=_new_reference())
    assert fake.post_calls == []


def test_c6_mismatch_does_not_take_lock_and_valid_charge_posts_once(db_session, customer, other_customer):
    with pytest.raises(AsaasCorrelatedPixChargeCustomerMismatchError):
        _charge(
            db_session,
            customer.id,
            FakeAsaas(),
            reference=_new_reference(),
            customer_id=_customer_id(other_customer.id),
        )
    assert _lock_row(db_session, customer.id) is None

    fake = FakeAsaas()
    _charge(db_session, customer.id, fake, reference=_new_reference())
    assert len(fake.customer_calls) == 1
    assert len(fake.post_calls) == 1


def test_c_customer_get_happens_before_claim_and_post(db_session, customer):
    order = []
    fake = FakeAsaas()
    original_get, original_post = fake.http_get, fake.http_post

    def get(request):
        order.append(request.operation)
        return original_get(request)

    def post(request):
        order.append(request.operation)
        return original_post(request)

    fake.http_get, fake.http_post = get, post
    _charge(db_session, customer.id, fake, reference=_new_reference())
    assert order == ["get_customer", "create_pix_payment", "get_pix_qr_code"]


# P1-B: BRL com no máximo 2 casas decimais, recusado antes de qualquer HTTP.
@pytest.mark.parametrize("amount", ["10.001", "49.905", "0.009"])
def test_charge_amount_with_more_than_two_decimals_is_rejected_without_http(db_session, customer, amount):
    fake = FakeAsaas()
    reference = _new_reference()
    with pytest.raises(ValueError):
        _charge(db_session, customer.id, fake, reference=reference, value=Decimal(amount))
    assert _no_http(fake)
    db_session.expire_all()
    assert (
        db_session.query(IdempotencyKey)
        .filter_by(key=asaas_payment_correlation_key(reference))
        .count()
        == 0
    )


@pytest.mark.parametrize("amount", ["10.10", "10.100", "49.9", "50"])
def test_charge_amount_with_two_decimals_or_less_posts_once(db_session, customer, amount):
    fake = FakeAsaas()
    _charge(db_session, customer.id, fake, reference=_new_reference(), value=Decimal(amount))
    assert len(fake.post_calls) == 1


@pytest.mark.parametrize("amount", ["10.001", "49.905"])
def test_endpoint_amount_with_more_than_two_decimals_is_422_without_http(
    db_session, customer, endpoint, charge_on, amount
):
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, amount=amount, idempotency_key="charge-key-0001")
    assert exc_info.value.status_code == 422
    assert _no_http(endpoint.fake)


def test_c_endpoint_invalid_customer_format_is_422_without_http(db_session, customer, endpoint, charge_on):
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, customer_id="cus_bad_format", idempotency_key="charge-key-0001")
    assert exc_info.value.status_code == 422
    assert _no_http(endpoint.fake)


def test_c_endpoint_customer_get_failure_is_503(db_session, customer, endpoint, charge_on):
    endpoint.fake.customer_response = AsaasSandboxTransportError("timeout")
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key="charge-key-0001")
    assert exc_info.value.status_code == 503
    assert endpoint.fake.post_calls == []


def test_c_endpoint_foreign_customer_is_403_without_leak(db_session, customer, other_customer, endpoint, charge_on):
    foreign = _customer_id(other_customer.id)
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, customer_id=foreign, idempotency_key="charge-key-0001")
    assert exc_info.value.status_code == 403
    detail = str(exc_info.value.detail)
    assert foreign not in detail
    assert API_KEY not in detail
    assert "agcus_" not in detail
    assert endpoint.fake.post_calls == []


def test_c_endpoint_pending_other_key_is_409_without_post(db_session, customer, endpoint, charge_on):
    endpoint.fake.post_response = AsaasSandboxTransportError("timeout")
    with pytest.raises(HTTPException):
        _call(db_session, customer, idempotency_key="charge-key-0001")

    endpoint.fake.post_response = (200, {"id": PAYMENT_ID})
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, customer, idempotency_key="charge-key-0002")
    assert exc_info.value.status_code == 409
    assert len(endpoint.fake.post_calls) == 1
    assert len(endpoint.fake.customer_calls) == 1
