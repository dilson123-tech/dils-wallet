"""
P0.5 — consulta/criação controlada do customer Asaas SANDBOX.

SQLite real em memória (StaticPool); transporte HTTP sempre fake.
Nenhum teste acessa a rede.

Garantias exercitadas:
- GET por externalReference SEMPRE antes de qualquer POST /customers;
- customer existente => nenhum POST;
- no máximo 1 POST por tentativa, sem retry;
- duplicidade / listagem ambígua => nunca POST;
- timeout/5xx/corpo inválido no POST => reconsulta única; inconclusiva
  mantém o lock e tentativas seguintes só fazem GET (nunca POST);
- flag ASAAS_SANDBOX_CUSTOMER_HTTP_ENABLED desligada => rota não faz
  HTTP de customer;
- mensagens de erro não expõem API key nem externalReference.
"""
import itertools
import json
import os

os.environ.setdefault("SECRET_KEY", "asaas-sandbox-customer-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request as StarletteRequest

from app.api.v1.routes import wallet as wallet_routes
from app.config import is_asaas_sandbox_customer_http_enabled
from app.core.rate_limit import limiter
from app.database import Base
from app.models.idempotency import IdempotencyKey
from app.models.user_main import User
from app.partner.asaas_client import AsaasSandboxClient
from app.partner.asaas_config import ASAAS_SANDBOX_BASE_URL, AsaasSandboxConfig
from app.partner.asaas_http_transport import AsaasSandboxTransportError
from app.services.asaas_correlated_pix_payment_service import (
    asaas_sandbox_customer_external_reference,
)
from app.services.asaas_sandbox_customer_service import (
    AsaasSandboxCustomerDuplicateError,
    AsaasSandboxCustomerIndeterminateError,
    AsaasSandboxCustomerPendingError,
    AsaasSandboxCustomerRejectedError,
    AsaasSandboxCustomerStorageError,
    AsaasSandboxCustomerUnavailableError,
    ensure_asaas_sandbox_customer,
)

API_KEY = "customer-api-key-must-never-leak"
PAYMENT_ID = "pay_sandbox0123456789"
QR_PAYLOAD = "00020101021226820014br.gov.bcb.pix2560sandbox-copia-e-cola"
QR_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
QR_EXPIRATION = "2026-12-31 23:59:59"
DUE_DATE = "2026-12-31"
PREPARED_VALUE = "49.90"
_CUSTOMER_PREFIX = "cus_sandboxuser"

TEST_CONFIG = AsaasSandboxConfig(
    env="sandbox",
    base_url=ASAAS_SANDBOX_BASE_URL,
    api_key=API_KEY,
    webhook_token="customer-webhook-token-must-never-leak",
    real_money_enabled=False,
    wallet_mode="partner",
    wallet_partner_provider="asaas",
)

_hosts = itertools.count(1)


def _customer_id(user_id: int) -> str:
    return f"{_CUSTOMER_PREFIX}{user_id}"


def _ref(user_id: int) -> str:
    return asaas_sandbox_customer_external_reference(user_id)


def _item(user_id: int, customer_id: str | None = None, **overrides) -> dict:
    item = {
        "id": customer_id or _customer_id(user_id),
        "externalReference": _ref(user_id),
        "deleted": False,
    }
    item.update(overrides)
    return item


def _page(*items, has_more=False) -> tuple:
    return (200, {"data": list(items), "totalCount": len(items), "hasMore": has_more})


def _created_customer(user_id: int):
    def respond(request):
        return 200, {**request.json, "id": _customer_id(user_id), "deleted": False}

    return respond


def _owned_customer(request):
    customer_id = request.url.rsplit("/", 1)[-1]
    owner = int(customer_id.removeprefix(_CUSTOMER_PREFIX))
    return 200, {"id": customer_id, "externalReference": _ref(owner), "deleted": False}


def _created_payment(request):
    return 200, {**request.json, "id": PAYMENT_ID, "status": "PENDING", "deleted": False}


class FakeAsaas:
    """
    Transporte fake. listings: respostas roteirizadas para cada GET de
    listagem de customers, consumidas em ordem (a última se repete).
    """

    def __init__(self, *, listings=None, create=None):
        self.listings = list(listings or [_page()])
        self.create_response = create
        self.customer_list_calls = []
        self.customer_post_calls = []
        self.ownership_calls = []
        self.payment_list_calls = []
        self.payment_post_calls = []
        self.qr_calls = []

    @staticmethod
    def _answer(response, request):
        if isinstance(response, BaseException):
            raise response
        if callable(response):
            return response(request)
        return response

    def http_get(self, request):
        if request.operation == "list_customers_by_external_reference":
            self.customer_list_calls.append(request)
            response = self.listings[0] if len(self.listings) == 1 else self.listings.pop(0)
            return self._answer(response, request)
        if request.operation == "get_customer":
            self.ownership_calls.append(request)
            return _owned_customer(request)
        if request.operation == "list_payments_by_external_reference":
            self.payment_list_calls.append(request)
            return _page()
        self.qr_calls.append(request)
        return 200, {
            "success": True,
            "encodedImage": QR_IMAGE,
            "payload": QR_PAYLOAD,
            "expirationDate": QR_EXPIRATION,
        }

    def http_post(self, request):
        if request.operation == "create_customer":
            self.customer_post_calls.append(request)
            if self.create_response is None:
                raise AssertionError("POST /customers inesperado")
            return self._answer(self.create_response, request)
        self.payment_post_calls.append(request)
        return _created_payment(request)


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
    user = User(email="asaas-sandbox-customer@test.local", hashed_password="x", role="customer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _ensure(db, user_id, fake):
    return ensure_asaas_sandbox_customer(
        db,
        client=AsaasSandboxClient(TEST_CONFIG),
        user_id=user_id,
        http_get=fake.http_get,
        http_post=fake.http_post,
    )


def _lock_rows(db) -> list:
    db.expire_all()
    return (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.key.like("asaas-sandbox-customer-pending:%"))
        .all()
    )


def _assert_safe_message(exc, user_id):
    text = repr(exc) + str(exc)
    assert API_KEY not in text
    assert _ref(user_id) not in text


# --- config ---------------------------------------------------------------


@pytest.mark.parametrize("value", [None, "", "false", "1", "yes", "truee", "on"])
def test_customer_flag_is_fail_closed(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("ASAAS_SANDBOX_CUSTOMER_HTTP_ENABLED", raising=False)
    else:
        monkeypatch.setenv("ASAAS_SANDBOX_CUSTOMER_HTTP_ENABLED", value)
    assert is_asaas_sandbox_customer_http_enabled() is False


@pytest.mark.parametrize("value", ["true", "TRUE", " True "])
def test_customer_flag_only_literal_true_enables(monkeypatch, value):
    monkeypatch.setenv("ASAAS_SANDBOX_CUSTOMER_HTTP_ENABLED", value)
    assert is_asaas_sandbox_customer_http_enabled() is True


# --- builder --------------------------------------------------------------


def test_list_builder_targets_sandbox_with_external_reference():
    client = AsaasSandboxClient(TEST_CONFIG)
    request = client.prepare_list_customers_by_external_reference(
        external_reference=_ref(7), limit=2
    )
    assert request.method == "GET"
    assert request.operation == "list_customers_by_external_reference"
    assert request.url.startswith(f"{ASAAS_SANDBOX_BASE_URL}/customers?")
    assert f"externalReference={_ref(7)}" in request.url
    assert "limit=2" in request.url


@pytest.mark.parametrize(
    "reference",
    ["", "agcus_", "agpay_" + "0" * 32, "agcus_" + "G" * 32, "agcus_" + "0" * 31, None],
)
def test_list_builder_rejects_invalid_reference(reference):
    client = AsaasSandboxClient(TEST_CONFIG)
    with pytest.raises(ValueError):
        client.prepare_list_customers_by_external_reference(external_reference=reference)


@pytest.mark.parametrize("limit", [0, 11, -1, True, "2", 2.0])
def test_list_builder_rejects_invalid_limit(limit):
    client = AsaasSandboxClient(TEST_CONFIG)
    with pytest.raises(ValueError):
        client.prepare_list_customers_by_external_reference(
            external_reference=_ref(1), limit=limit
        )


# --- service: existente / criação -------------------------------------------


def test_existing_customer_is_returned_without_post(db_session, customer):
    fake = FakeAsaas(listings=[_page(_item(customer.id))])

    assert _ensure(db_session, customer.id, fake) == _customer_id(customer.id)
    assert len(fake.customer_list_calls) == 1
    assert fake.customer_post_calls == []
    assert _lock_rows(db_session) == []


def test_deleted_customer_is_ignored_and_new_one_created(db_session, customer):
    fake = FakeAsaas(
        listings=[_page(_item(customer.id, "cus_old1", deleted=True))],
        create=_created_customer(customer.id),
    )

    assert _ensure(db_session, customer.id, fake) == _customer_id(customer.id)
    assert len(fake.customer_post_calls) == 1


def test_absent_customer_is_created_with_single_post_and_fake_data(db_session, customer):
    fake = FakeAsaas(create=_created_customer(customer.id))

    assert _ensure(db_session, customer.id, fake) == _customer_id(customer.id)

    assert len(fake.customer_list_calls) == 1
    assert len(fake.customer_post_calls) == 1
    post = fake.customer_post_calls[0]
    assert post.method == "POST"
    assert post.url == f"{ASAAS_SANDBOX_BASE_URL}/customers"
    assert post.json["externalReference"] == _ref(customer.id)
    # Dados fictícios de sandbox; nenhum dado real do usuário.
    assert post.json["email"].endswith("@example.com")
    assert customer.email not in json.dumps(post.json)
    assert _lock_rows(db_session) == []


def test_get_always_happens_before_post(db_session, customer):
    order = []
    fake = FakeAsaas(create=_created_customer(customer.id))
    get, post = fake.http_get, fake.http_post
    fake.http_get = lambda r: (order.append("GET"), get(r))[1]
    fake.http_post = lambda r: (order.append("POST"), post(r))[1]

    _ensure(db_session, customer.id, fake)

    assert order == ["GET", "POST"]


def test_second_call_after_creation_reuses_customer_without_post(db_session, customer):
    fake = FakeAsaas(
        listings=[_page(), _page(_item(customer.id))],
        create=_created_customer(customer.id),
    )

    _ensure(db_session, customer.id, fake)
    assert _ensure(db_session, customer.id, fake) == _customer_id(customer.id)
    assert len(fake.customer_post_calls) == 1


# --- service: duplicidade / listagem inválida -------------------------------


@pytest.mark.parametrize(
    "listing_factory",
    [
        lambda uid: _page(_item(uid, "cus_a1"), _item(uid, "cus_b2")),
        lambda uid: _page(_item(uid, "cus_a1"), has_more=True),
        lambda uid: _page(has_more=True),
    ],
    ids=["two-active", "has-more", "has-more-empty"],
)
def test_duplicate_listing_never_posts(db_session, customer, listing_factory):
    fake = FakeAsaas(listings=[listing_factory(customer.id)])

    with pytest.raises(AsaasSandboxCustomerDuplicateError) as exc:
        _ensure(db_session, customer.id, fake)

    assert fake.customer_post_calls == []
    assert _lock_rows(db_session) == []
    _assert_safe_message(exc.value, customer.id)


@pytest.mark.parametrize(
    "response",
    [
        AsaasSandboxTransportError("timeout"),
        TimeoutError("timeout"),
        (500, {"errors": []}),
        (404, {}),
        (200, None),
        (200, {"data": "x"}),
        (200, {}),
        (True, {"data": []}),
        (200, {"data": ["not-a-dict"]}),
        (200, {"data": [{"id": "invalid", "externalReference": "x"}]}),
    ],
)
def test_unreliable_first_listing_is_unavailable_without_post(db_session, customer, response):
    fake = FakeAsaas(listings=[response])

    with pytest.raises(AsaasSandboxCustomerUnavailableError) as exc:
        _ensure(db_session, customer.id, fake)

    assert fake.customer_post_calls == []
    assert _lock_rows(db_session) == []
    _assert_safe_message(exc.value, customer.id)


def test_foreign_external_reference_invalidates_listing(db_session, customer):
    other = customer.id + 1000
    fake = FakeAsaas(listings=[_page(_item(other))])

    with pytest.raises(AsaasSandboxCustomerUnavailableError):
        _ensure(db_session, customer.id, fake)

    assert fake.customer_post_calls == []


def test_invalid_customer_id_in_listing_is_unavailable(db_session, customer):
    fake = FakeAsaas(listings=[_page(_item(customer.id, "cus_bad id!"))])

    with pytest.raises(AsaasSandboxCustomerUnavailableError):
        _ensure(db_session, customer.id, fake)

    assert fake.customer_post_calls == []


# --- service: desfechos do POST --------------------------------------------


@pytest.mark.parametrize("status", [400, 401, 409, 422])
def test_post_4xx_is_rejected_and_releases_lock(db_session, customer, status):
    fake = FakeAsaas(create=(status, {"errors": [{"description": API_KEY}]}))

    with pytest.raises(AsaasSandboxCustomerRejectedError) as exc:
        _ensure(db_session, customer.id, fake)

    assert len(fake.customer_post_calls) == 1
    assert len(fake.customer_list_calls) == 1
    assert _lock_rows(db_session) == []
    _assert_safe_message(exc.value, customer.id)


@pytest.mark.parametrize(
    "create",
    [
        AsaasSandboxTransportError("timeout"),
        (500, {}),
        (503, None),
        (200, None),
        (200, {"id": "invalid"}),
        (200, {"id": "cus_x1", "externalReference": "agcus_" + "f" * 32}),
        (201, {"id": "cus_x1", "deleted": True}),
    ],
)
def test_uncertain_post_with_recheck_finding_customer_returns_it(db_session, customer, create):
    fake = FakeAsaas(
        listings=[_page(), _page(_item(customer.id))],
        create=create,
    )

    assert _ensure(db_session, customer.id, fake) == _customer_id(customer.id)
    assert len(fake.customer_post_calls) == 1
    assert len(fake.customer_list_calls) == 2
    assert _lock_rows(db_session) == []


@pytest.mark.parametrize(
    "recheck",
    [_page(), AsaasSandboxTransportError("timeout"), (500, {})],
    ids=["empty", "timeout", "5xx"],
)
def test_uncertain_post_with_inconclusive_recheck_keeps_lock(db_session, customer, recheck):
    fake = FakeAsaas(
        listings=[_page(), recheck],
        create=AsaasSandboxTransportError("timeout"),
    )

    with pytest.raises(AsaasSandboxCustomerIndeterminateError) as exc:
        _ensure(db_session, customer.id, fake)

    assert len(fake.customer_post_calls) == 1
    assert len(_lock_rows(db_session)) == 1
    _assert_safe_message(exc.value, customer.id)

    # Tentativa seguinte: lock mantido => apenas GET, nunca POST.
    fake.listings = [_page()]
    with pytest.raises(AsaasSandboxCustomerPendingError):
        _ensure(db_session, customer.id, fake)
    assert len(fake.customer_post_calls) == 1
    assert len(_lock_rows(db_session)) == 1


def test_uncertain_post_with_duplicate_recheck_keeps_lock(db_session, customer):
    fake = FakeAsaas(
        listings=[_page(), _page(_item(customer.id, "cus_a1"), _item(customer.id, "cus_b2"))],
        create=(500, {}),
    )

    with pytest.raises(AsaasSandboxCustomerDuplicateError):
        _ensure(db_session, customer.id, fake)

    assert len(fake.customer_post_calls) == 1
    assert len(_lock_rows(db_session)) == 1


def test_held_lock_is_released_once_get_proves_customer(db_session, customer):
    fake = FakeAsaas(listings=[_page(), _page()], create=(502, {}))
    with pytest.raises(AsaasSandboxCustomerIndeterminateError):
        _ensure(db_session, customer.id, fake)
    assert len(_lock_rows(db_session)) == 1

    fake.listings = [_page(_item(customer.id))]
    assert _ensure(db_session, customer.id, fake) == _customer_id(customer.id)
    assert _lock_rows(db_session) == []
    assert len(fake.customer_post_calls) == 1


@pytest.mark.parametrize(
    "listing,error",
    [
        (AsaasSandboxTransportError("timeout"), AsaasSandboxCustomerPendingError),
        (lambda r: _page(has_more=True), AsaasSandboxCustomerDuplicateError),
    ],
)
def test_held_lock_never_posts(db_session, customer, listing, error):
    fake = FakeAsaas(listings=[_page(), _page()], create=(500, {}))
    with pytest.raises(AsaasSandboxCustomerIndeterminateError):
        _ensure(db_session, customer.id, fake)

    fake.listings = [listing]
    with pytest.raises(error):
        _ensure(db_session, customer.id, fake)
    assert len(fake.customer_post_calls) == 1
    assert len(_lock_rows(db_session)) == 1


def test_lock_is_per_user(db_session, customer):
    fake = FakeAsaas(listings=[_page(), _page()], create=(500, {}))
    with pytest.raises(AsaasSandboxCustomerIndeterminateError):
        _ensure(db_session, customer.id, fake)

    other = customer.id + 1
    other_fake = FakeAsaas(create=_created_customer(other))
    assert _ensure(db_session, other, other_fake) == _customer_id(other)
    assert len(other_fake.customer_post_calls) == 1


def test_storage_failure_on_lock_never_calls_http(db_session, customer, monkeypatch):
    from sqlalchemy.exc import OperationalError

    def broken_flush(*args, **kwargs):
        raise OperationalError("INSERT", {}, Exception("db down"))

    monkeypatch.setattr(db_session, "flush", broken_flush)
    fake = FakeAsaas(create=_created_customer(customer.id))

    with pytest.raises(AsaasSandboxCustomerStorageError):
        _ensure(db_session, customer.id, fake)

    assert fake.customer_list_calls == []
    assert fake.customer_post_calls == []


# --- rota -------------------------------------------------------------------


@pytest.fixture()
def endpoint(monkeypatch):
    limiter.reset()
    monkeypatch.setattr(wallet_routes, "load_asaas_sandbox_config", lambda: TEST_CONFIG)
    monkeypatch.delenv("ASAAS_SANDBOX_CHARGE_HTTP_ENABLED", raising=False)
    monkeypatch.delenv("ASAAS_SANDBOX_CUSTOMER_HTTP_ENABLED", raising=False)
    state = SimpleNamespace(fake=FakeAsaas(), built=[])

    def build(config):
        state.built.append(config)
        return SimpleNamespace(post=state.fake.http_post, get=state.fake.http_get)

    monkeypatch.setattr(wallet_routes, "_build_asaas_sandbox_charge_transport", build)
    yield state
    limiter.reset()


@pytest.fixture()
def charge_on(monkeypatch):
    monkeypatch.setenv("ASAAS_SANDBOX_CHARGE_HTTP_ENABLED", "true")


@pytest.fixture()
def customer_on(monkeypatch):
    monkeypatch.setenv("ASAAS_SANDBOX_CUSTOMER_HTTP_ENABLED", "true")


def _request() -> StarletteRequest:
    host = f"198.51.100.{next(_hosts) % 250 + 1}"
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


def _call(db, user, *, customer_id=None, idempotency_key="customer-key-0001"):
    return wallet_routes.prepare_wallet_asaas_correlated_pix_payment(
        request=_request(),
        payload=wallet_routes.WalletAsaasCorrelatedPixPaymentPreparationIn(
            customer_id=customer_id,
            amount=Decimal(PREPARED_VALUE),
            due_date=DUE_DATE,
        ),
        current_user=SimpleNamespace(id=user.id),
        db=db,
        idempotency_key=idempotency_key,
    )


def test_route_customer_flag_on_creates_customer_then_charge(
    db_session, customer, endpoint, charge_on, customer_on
):
    endpoint.fake.create_response = _created_customer(customer.id)

    response = _call(db_session, customer)

    fake = endpoint.fake
    assert len(fake.customer_list_calls) == 1
    assert len(fake.customer_post_calls) == 1
    # Ownership continua validada no fluxo de cobrança.
    assert len(fake.ownership_calls) == 1
    assert fake.ownership_calls[0].url.endswith(f"/customers/{_customer_id(customer.id)}")
    assert len(fake.payment_post_calls) == 1
    assert fake.payment_post_calls[0].json["customer"] == _customer_id(customer.id)
    assert response["operation"] == "create_asaas_correlated_pix_charge"
    text = json.dumps(response)
    assert _customer_id(customer.id) not in text
    assert _ref(customer.id) not in text
    assert API_KEY not in text


def test_route_customer_flag_on_reuses_existing_customer(
    db_session, customer, endpoint, charge_on, customer_on
):
    endpoint.fake.listings = [_page(_item(customer.id))]

    _call(db_session, customer)

    assert endpoint.fake.customer_post_calls == []
    assert len(endpoint.fake.payment_post_calls) == 1


def test_route_explicit_customer_id_skips_ensure(
    db_session, customer, endpoint, charge_on, customer_on
):
    _call(db_session, customer, customer_id=_customer_id(customer.id))

    assert endpoint.fake.customer_list_calls == []
    assert endpoint.fake.customer_post_calls == []
    assert len(endpoint.fake.ownership_calls) == 1


def test_route_customer_flag_off_requires_customer_id_without_http(
    db_session, customer, endpoint, charge_on
):
    with pytest.raises(HTTPException) as exc:
        _call(db_session, customer)

    assert exc.value.status_code == 422
    assert endpoint.fake.customer_list_calls == []
    assert endpoint.fake.customer_post_calls == []
    assert endpoint.fake.payment_post_calls == []


def test_route_local_path_never_resolves_customer(db_session, customer, endpoint, customer_on):
    with pytest.raises(HTTPException) as exc:
        _call(db_session, customer)

    assert exc.value.status_code == 422
    assert endpoint.built == []
    assert endpoint.fake.customer_list_calls == []


@pytest.mark.parametrize(
    "listings,create,status",
    [
        ([_page(has_more=True)], None, 409),
        ([_page(), _page()], (500, {}), 409),
        ([_page()], (400, {}), 502),
        ([(500, {})], None, 503),
    ],
    ids=["duplicate", "indeterminate", "rejected", "unavailable"],
)
def test_route_maps_customer_errors_without_charging(
    db_session, customer, endpoint, charge_on, customer_on, listings, create, status
):
    endpoint.fake.listings = listings
    endpoint.fake.create_response = create

    with pytest.raises(HTTPException) as exc:
        _call(db_session, customer)

    assert exc.value.status_code == status
    assert endpoint.fake.payment_post_calls == []
    assert endpoint.fake.ownership_calls == []
    assert API_KEY not in str(exc.value.detail)
    assert _ref(customer.id) not in str(exc.value.detail)


def test_route_pending_after_indeterminate_is_409_without_post(
    db_session, customer, endpoint, charge_on, customer_on
):
    endpoint.fake.listings = [_page(), _page()]
    endpoint.fake.create_response = (500, {})
    with pytest.raises(HTTPException):
        _call(db_session, customer)

    endpoint.fake.listings = [_page()]
    with pytest.raises(HTTPException) as exc:
        _call(db_session, customer, idempotency_key="customer-key-0002")

    assert exc.value.status_code == 409
    assert len(endpoint.fake.customer_post_calls) == 1
    assert endpoint.fake.payment_post_calls == []
