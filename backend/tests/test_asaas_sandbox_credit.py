"""
P0.3 — crédito idempotente no ledger a partir do webhook Asaas SANDBOX.

SQLite real em memória (StaticPool). O handler é chamado diretamente
(mesmo padrão de test_asaas_webhook_receiver.py, um client host por
teste para isolar o rate limit) e a correlação é criada pelo fluxo real
prepare_asaas_correlated_pix_payment, sem nenhuma chamada HTTP.

Garantias exercitadas:
- flag ASAAS_SANDBOX_CREDIT_ENABLED ausente/!= "true" => resposta e
  ledger inalterados;
- payment_id é a identidade financeira: crédito no máximo uma vez por
  payment_id e por cobrança preparada;
- valor vem SEMPRE da cobrança preparada; payload divergente falha
  fechado;
- evento, chaves de crédito e linha de ledger no mesmo commit.
"""
import itertools
import json
import os

os.environ.setdefault("SECRET_KEY", "asaas-sandbox-credit-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request as StarletteRequest

from app.api.v1.routes import wallet as wallet_routes
from app.core.rate_limit import limiter
from app.database import Base, get_db
from app.main import app
from app.models.idempotency import IdempotencyKey
from app.models.pix_ledger import PixLedger
from app.models.user_main import User
from app.partner.asaas_client import AsaasSandboxClient
from app.partner.asaas_config import ASAAS_SANDBOX_BASE_URL, AsaasSandboxConfig
from app.partner.asaas_payment_correlation import (
    build_asaas_payment_user_correlation_record,
    resolve_asaas_payment_user_correlation,
)
from app.services.asaas_correlated_pix_payment_service import (
    prepare_asaas_correlated_pix_payment,
)
from app.utils.security import create_access_token

WEBHOOK_TOKEN = "sandbox-credit-webhook-token"
CUSTOMER_EMAIL = "asaas-sandbox-credit@test.local"
PREPARED_VALUE = "49.90"
CREDIT_PREFIX = "asaas-sandbox-credit"

TEST_CONFIG = AsaasSandboxConfig(
    env="sandbox",
    base_url=ASAAS_SANDBOX_BASE_URL,
    api_key="sandbox-api-key-for-test-only",
    webhook_token="sandbox-webhook-token-for-test-only",
    real_money_enabled=False,
    wallet_mode="partner",
    wallet_partner_provider="asaas",
)

_hosts = itertools.count(1)
_refs = itertools.count(1)


def _request() -> StarletteRequest:
    host = f"198.51.100.{next(_hosts) % 250 + 1}"
    path = "/api/v1/partners/asaas/webhooks/sandbox"
    scope = {
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
    return StarletteRequest(scope)


def _new_reference() -> str:
    return f"agpay_{next(_refs):032x}"


@pytest.fixture(autouse=True)
def _webhook_config(monkeypatch):
    limiter.reset()
    monkeypatch.setattr(
        wallet_routes,
        "load_asaas_sandbox_config",
        lambda: SimpleNamespace(webhook_token=WEBHOOK_TOKEN, env="sandbox"),
    )
    monkeypatch.delenv("ASAAS_SANDBOX_CREDIT_ENABLED", raising=False)
    yield
    limiter.reset()


@pytest.fixture()
def credit_on(monkeypatch):
    monkeypatch.setenv("ASAAS_SANDBOX_CREDIT_ENABLED", "true")


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
    user = User(email=CUSTOMER_EMAIL, hashed_password="x", role="customer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _prepare(db, user_id: int, value=Decimal(PREPARED_VALUE)) -> str:
    reference = _new_reference()
    prepare_asaas_correlated_pix_payment(
        db,
        client=AsaasSandboxClient(TEST_CONFIG),
        user_id=user_id,
        customer_id="cus_sandbox_test",
        value=value,
        due_date="2026-12-31",
        description="Cobrança sandbox teste",
        external_reference=reference,
    )
    return reference


def _payload(reference, *, event_id="evt_credit_1", payment_id="pay_credit_1", **payment_overrides):
    payment = {
        "id": payment_id,
        "status": "RECEIVED",
        "billingType": "PIX",
        "value": PREPARED_VALUE,
        "externalReference": reference,
    }
    payment.update(payment_overrides)
    payment = {k: v for k, v in payment.items() if v is not None}
    return {"id": event_id, "event": "PAYMENT_RECEIVED", "payment": payment}


def _send(db, payload):
    return wallet_routes.handle_asaas_sandbox_webhook_receiver(
        request=_request(),
        payload=payload,
        db=db,
        asaas_access_token=WEBHOOK_TOKEN,
    )


def _ledger(db) -> list:
    return db.query(PixLedger).all()


def _saldo(db, user_id: int) -> Decimal:
    saldo = Decimal("0")
    for row in db.query(PixLedger).filter(PixLedger.user_id == user_id).all():
        amount = Decimal(str(row.amount))
        saldo += amount if row.kind == "credit" else -amount
    return saldo


def _credit_keys(db) -> list:
    return (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.key.like(f"{CREDIT_PREFIX}%"))
        .all()
    )


# --- flag -----------------------------------------------------------------


@pytest.mark.parametrize("value", [None, "", "false", "1", "yes", "on", "truee"])
def test_flag_not_true_never_credits(db_session, customer, monkeypatch, value):
    if value is not None:
        monkeypatch.setenv("ASAAS_SANDBOX_CREDIT_ENABLED", value)
    reference = _prepare(db_session, customer.id)

    response = _send(db_session, _payload(reference))

    assert "credit" not in response
    assert response["can_credit_balance"] is False
    assert _ledger(db_session) == []
    assert _credit_keys(db_session) == []


@pytest.mark.parametrize("value", ["true", "TRUE", " True "])
def test_flag_true_credits_once(db_session, customer, monkeypatch, value):
    monkeypatch.setenv("ASAAS_SANDBOX_CREDIT_ENABLED", value)
    reference = _prepare(db_session, customer.id)

    response = _send(db_session, _payload(reference))

    credit = response["credit"]
    assert credit["status"] == "credited"
    assert credit["credited"] is True
    assert credit["new_credit"] is True
    assert credit["replayed"] is False
    assert credit["amount"] == PREPARED_VALUE
    assert credit["currency"] == "BRL"
    assert credit["amount_source"] == "prepared_payment"
    assert credit["real_money_enabled"] is False
    assert response["can_credit_balance"] is True

    rows = _ledger(db_session)
    assert len(rows) == 1
    assert rows[0].kind == "credit"
    assert rows[0].user_id == customer.id
    assert Decimal(str(rows[0].amount)) == Decimal(PREPARED_VALUE)
    assert _saldo(db_session, customer.id) == Decimal(PREPARED_VALUE)
    # chave por payment_id + chave por cobrança preparada
    assert len(_credit_keys(db_session)) == 2


# --- idempotência -----------------------------------------------------------


def test_same_event_replay_does_not_credit_again(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id)
    payload = _payload(reference)
    _send(db_session, payload)

    replay = _send(db_session, payload)

    assert replay["duplicated"] is True
    assert replay["credit"]["replayed"] is True
    assert replay["credit"]["new_credit"] is False
    assert replay["can_credit_balance"] is False
    assert len(_ledger(db_session)) == 1
    assert _saldo(db_session, customer.id) == Decimal(PREPARED_VALUE)


def test_new_event_same_payment_id_is_already_credited(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id)
    _send(db_session, _payload(reference, event_id="evt_a"))

    response = _send(db_session, _payload(reference, event_id="evt_b"))

    assert response["credit"]["status"] == "already_credited"
    assert response["credit"]["credited"] is False
    assert response["can_credit_balance"] is False
    assert len(_ledger(db_session)) == 1


def test_new_payment_id_same_prepared_charge_is_already_credited(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id)
    _send(db_session, _payload(reference, event_id="evt_a", payment_id="pay_a"))

    response = _send(db_session, _payload(reference, event_id="evt_b", payment_id="pay_b"))

    assert response["credit"]["status"] == "already_credited"
    assert len(_ledger(db_session)) == 1
    assert _saldo(db_session, customer.id) == Decimal(PREPARED_VALUE)


def test_distinct_prepared_charges_credit_independently(db_session, customer, credit_on):
    first = _prepare(db_session, customer.id)
    second = _prepare(db_session, customer.id)

    _send(db_session, _payload(first, event_id="evt_a", payment_id="pay_a"))
    _send(db_session, _payload(second, event_id="evt_b", payment_id="pay_b"))

    assert len(_ledger(db_session)) == 2
    assert _saldo(db_session, customer.id) == Decimal("99.80")


def test_flag_off_then_on_new_event_credits_once(db_session, customer, monkeypatch):
    reference = _prepare(db_session, customer.id)
    _send(db_session, _payload(reference, event_id="evt_off"))
    assert _ledger(db_session) == []

    monkeypatch.setenv("ASAAS_SANDBOX_CREDIT_ENABLED", "true")
    # replay do evento processado com a flag desligada não credita
    replay = _send(db_session, _payload(reference, event_id="evt_off"))
    assert "credit" not in replay
    assert _ledger(db_session) == []

    _send(db_session, _payload(reference, event_id="evt_on"))
    _send(db_session, _payload(reference, event_id="evt_on_2"))
    assert len(_ledger(db_session)) == 1


# --- fail-closed ------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides,expected",
    [
        ({"value": "49.91"}, "amount_mismatch"),
        ({"value": "4990"}, "amount_mismatch"),
        ({"value": "abc"}, "amount_mismatch"),
        ({"value": None}, "amount_mismatch"),
        ({"billingType": "BOLETO"}, "billing_type_not_pix"),
        ({"billingType": None}, "billing_type_not_pix"),
        ({"status": "PENDING"}, "payment_status_not_received"),
        ({"status": "CONFIRMED"}, "payment_status_not_received"),
        ({"id": None}, "payment_id_missing"),
        ({"id": "   "}, "payment_id_missing"),
    ],
)
def test_ineligible_payment_fails_closed(db_session, customer, credit_on, overrides, expected):
    reference = _prepare(db_session, customer.id)
    payload = _payload(reference)
    payload["payment"].update(overrides)
    payload["payment"] = {k: v for k, v in payload["payment"].items() if v is not None}

    response = _send(db_session, payload)

    assert response["credit"]["status"] == expected
    assert response["credit"]["credited"] is False
    assert response["credit"]["amount"] is None
    assert response["can_credit_balance"] is False
    assert _ledger(db_session) == []
    assert _credit_keys(db_session) == []


@pytest.mark.parametrize("reference", ["agpay_" + "f" * 32, "not-a-reference", None])
def test_unknown_or_missing_reference_is_unresolved(db_session, customer, credit_on, reference):
    response = _send(db_session, _payload(reference))

    assert response["credit"]["status"] == "unresolved"
    assert _ledger(db_session) == []


def test_legacy_correlation_without_prepared_amount_fails_closed(db_session, customer, credit_on):
    reference = _new_reference()
    db_session.add(
        build_asaas_payment_user_correlation_record(
            user_id=customer.id,
            external_reference=reference,
        )
    )
    db_session.commit()

    response = _send(db_session, _payload(reference))

    assert response["credit"]["status"] == "amount_unavailable"
    assert _ledger(db_session) == []


def test_tampered_prepared_amount_fails_closed(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id)
    record = db_session.query(IdempotencyKey).filter(
        IdempotencyKey.key.like("asaas-payment-correlation:%")
    ).one()
    stored = json.loads(record.response_json)
    stored["prepared_amount"] = "4990.00"
    record.response_json = json.dumps(stored)
    record.request_hash = "0" * 64
    db_session.commit()

    response = _send(db_session, _payload(reference, value="4990.00"))

    assert response["credit"]["status"] == "amount_unavailable"
    assert _ledger(db_session) == []


def test_deleted_user_fails_closed(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id)
    db_session.delete(customer)
    db_session.commit()

    response = _send(db_session, _payload(reference))

    assert response["credit"]["status"] == "user_not_found"
    assert _ledger(db_session) == []


def test_non_received_event_type_is_not_applicable(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id)
    payload = _payload(reference)
    payload["event"] = "PAYMENT_CREATED"

    response = _send(db_session, payload)

    assert response["credit"]["credited"] is False
    assert _ledger(db_session) == []


# --- atomicidade ------------------------------------------------------------


def test_commit_failure_rolls_back_event_credit_and_ledger(db_session, customer, credit_on, monkeypatch):
    reference = _prepare(db_session, customer.id)
    keys_before = db_session.query(IdempotencyKey).count()

    def _failing_commit():
        raise OperationalError("COMMIT", {}, Exception("simulated"))

    monkeypatch.setattr(db_session, "commit", _failing_commit)
    with pytest.raises(HTTPException) as exc:
        _send(db_session, _payload(reference))
    monkeypatch.undo()
    monkeypatch.setenv("ASAAS_SANDBOX_CREDIT_ENABLED", "true")
    monkeypatch.setattr(
        wallet_routes,
        "load_asaas_sandbox_config",
        lambda: SimpleNamespace(webhook_token=WEBHOOK_TOKEN, env="sandbox"),
    )

    assert exc.value.status_code == 503
    assert exc.value.headers == {"Retry-After": "30"}
    assert _ledger(db_session) == []
    assert _credit_keys(db_session) == []
    assert db_session.query(IdempotencyKey).count() == keys_before

    # retry após a falha credita exatamente uma vez
    response = _send(db_session, _payload(reference))
    assert response["credit"]["status"] == "credited"
    assert len(_ledger(db_session)) == 1


def test_concurrent_credit_key_conflict_rolls_back_everything(db_session, customer, credit_on, monkeypatch):
    reference = _prepare(db_session, customer.id)
    keys_before = db_session.query(IdempotencyKey).count()
    original_decision = wallet_routes._asaas_sandbox_credit_decision

    def _racing_decision(db, **kwargs):
        result = original_decision(db, **kwargs)
        status, _amount, credit_keys = result
        assert status == "eligible"
        # outro evento do mesmo pagamento grava a chave entre a decisão
        # e o commit deste request
        db.add(IdempotencyKey(key=credit_keys[0], request_hash="race"))
        db.flush()
        return result

    monkeypatch.setattr(wallet_routes, "_asaas_sandbox_credit_decision", _racing_decision)

    with pytest.raises(HTTPException) as exc:
        _send(db_session, _payload(reference))

    assert exc.value.status_code == 503
    assert _ledger(db_session) == []
    assert db_session.query(IdempotencyKey).count() == keys_before


# --- privacidade / preparação ----------------------------------------------


def test_response_does_not_leak_sensitive_values(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id)
    payload = _payload(reference, event_id="evt_secret_xyz", payment_id="pay_secret_xyz")

    first = json.dumps(_send(db_session, payload), default=str)
    replay = json.dumps(_send(db_session, payload), default=str)

    for body in (first, replay):
        for secret in ("pay_secret_xyz", "evt_secret_xyz", reference, WEBHOOK_TOKEN):
            assert secret not in body
        assert "correlation_storage" not in body

    for row in _credit_keys(db_session):
        for secret in ("pay_secret_xyz", "evt_secret_xyz", reference):
            assert secret not in row.key
            assert secret not in (row.response_json or "")


def test_preparation_stores_prepared_amount(db_session, customer):
    reference = _prepare(db_session, customer.id)

    correlation = resolve_asaas_payment_user_correlation(
        db_session, external_reference=reference
    )

    assert correlation.prepared_amount == Decimal(PREPARED_VALUE)


def test_preparation_with_sub_cent_value_stores_no_amount(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id, value=Decimal("49.901"))

    correlation = resolve_asaas_payment_user_correlation(
        db_session, external_reference=reference
    )
    assert correlation.prepared_amount is None

    response = _send(db_session, _payload(reference, value="49.90"))
    assert response["credit"]["status"] == "amount_unavailable"
    assert _ledger(db_session) == []


# --- consistência com as rotas de leitura ----------------------------------


def test_balance_and_history_reflect_single_credit(db_session, customer, credit_on):
    reference = _prepare(db_session, customer.id)
    payload = _payload(reference)
    _send(db_session, payload)
    _send(db_session, payload)
    _send(db_session, _payload(reference, event_id="evt_other"))

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {create_access_token({'sub': CUSTOMER_EMAIL})}"}
        balance = client.get("/api/v1/pix/balance", headers=headers)
        history = client.get("/api/v1/pix/history", headers=headers)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert balance.status_code == 200, balance.text
    assert Decimal(str(balance.json()["saldo"])) == Decimal(PREPARED_VALUE)

    assert history.status_code == 200, history.text
    items = history.json()
    entradas = [i for i in items if i.get("tipo") == "entrada"]
    assert len(entradas) == 1
    assert Decimal(str(entradas[0]["valor"])) == Decimal(PREPARED_VALUE)


# --- extrato/histórico: crédito sandbox aparece uma única vez ---------------
#
# Fontes de leitura existentes (auditadas no P0.3):
# - PixLedger: /api/v1/wallet/history, /api/v1/wallet/balance,
#   /api/v1/pix/history e /api/v1/pix/balance. É a ÚNICA fonte do crédito
#   financeiro e é o que estes testes contam.
# - /api/v1/wallet/structured-statement (provider sandbox): item VIRTUAL
#   derivado dos eventos de webhook (_asaas_sandbox_statement_items_from_
#   webhooks). NÃO lê o PixLedger e nenhum consumidor mescla as duas
#   fontes. Por isso esse item virtual é uma fonte separada e NÃO deve ser
#   contado como duplicidade do crédito no ledger enquanto não existir
#   merge entre as fontes. Se um dia as fontes forem mescladas, estes
#   testes precisam passar a cobrir a deduplicação do resultado mesclado.


def _read_views(db, monkeypatch) -> dict:
    from app.partner.sandbox_adapter import InternalSandboxPartnerAdapter

    monkeypatch.setattr(
        wallet_routes,
        "get_partner_adapter",
        lambda: InternalSandboxPartnerAdapter(),
    )

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {create_access_token({'sub': CUSTOMER_EMAIL})}"}
        views = {}
        for name, path in (
            ("wallet_history", "/api/v1/wallet/history"),
            ("wallet_balance", "/api/v1/wallet/balance"),
            ("pix_history", "/api/v1/pix/history"),
            ("pix_balance", "/api/v1/pix/balance"),
            ("structured_statement", "/api/v1/wallet/structured-statement"),
        ):
            response = client.get(path, headers=headers)
            assert response.status_code == 200, (path, response.text)
            views[name] = response.json()
        return views
    finally:
        app.dependency_overrides.pop(get_db, None)


def _assert_single_ledger_credit(views) -> None:
    expected = Decimal(PREPARED_VALUE)

    wallet_history = views["wallet_history"]["history"]
    assert len(wallet_history) == 1
    assert wallet_history[0]["kind"] == "credit"
    assert wallet_history[0]["description"] == "PIX Asaas Sandbox recebido"
    assert Decimal(str(wallet_history[0]["amount"])) == expected

    pix_history = views["pix_history"]
    assert len(pix_history) == 1
    assert pix_history[0]["tipo"] == "entrada"
    assert Decimal(str(pix_history[0]["valor"])) == expected

    assert Decimal(str(views["wallet_balance"]["balance"])) == expected
    assert Decimal(str(views["pix_balance"]["saldo"])) == expected


def _virtual_statement_items(views) -> list:
    return [
        item
        for item in views["structured_statement"]["statement"]["items"]
        if item["description"] == "PIX Asaas Sandbox recebido"
    ]


def test_credited_payment_appears_once_in_ledger_views(db_session, customer, credit_on, monkeypatch):
    reference = _prepare(db_session, customer.id)
    _send(db_session, _payload(reference))

    views = _read_views(db_session, monkeypatch)

    _assert_single_ledger_credit(views)
    # Fonte separada (ver comentário da seção): um item virtual por
    # cobrança, não somado ao ledger.
    assert len(_virtual_statement_items(views)) == 1


def test_same_event_replay_keeps_single_entry(db_session, customer, credit_on, monkeypatch):
    reference = _prepare(db_session, customer.id)
    payload = _payload(reference)
    _send(db_session, payload)
    replay = _send(db_session, payload)
    assert replay["duplicated"] is True

    views = _read_views(db_session, monkeypatch)

    _assert_single_ledger_credit(views)
    assert len(_virtual_statement_items(views)) == 1


def test_new_event_same_payment_id_keeps_single_entry(db_session, customer, credit_on, monkeypatch):
    reference = _prepare(db_session, customer.id)
    _send(db_session, _payload(reference))
    second = _send(db_session, _payload(reference, event_id="evt_credit_2"))
    assert second["duplicated"] is False

    views = _read_views(db_session, monkeypatch)

    _assert_single_ledger_credit(views)
    assert len(_credit_keys(db_session)) == 2  # payment_id + cobrança
    assert len(_virtual_statement_items(views)) == 1


def test_flag_false_keeps_previous_statement_behavior(db_session, customer, monkeypatch):
    monkeypatch.setenv("ASAAS_SANDBOX_CREDIT_ENABLED", "false")
    reference = _prepare(db_session, customer.id)
    _send(db_session, _payload(reference))
    _send(db_session, _payload(reference))

    views = _read_views(db_session, monkeypatch)

    # Comportamento anterior ao P0.3: nada no ledger, saldo zero...
    assert views["wallet_history"]["history"] == []
    assert views["pix_history"] == []
    assert Decimal(str(views["wallet_balance"]["balance"])) == Decimal("0")
    assert Decimal(str(views["pix_balance"]["saldo"])) == Decimal("0")
    assert _credit_keys(db_session) == []
    # ...e o item virtual do structured-statement continua existindo,
    # como já existia antes do P0.3.
    virtual = _virtual_statement_items(views)
    assert len(virtual) == 1
    assert Decimal(str(virtual[0]["amount"])) == Decimal(PREPARED_VALUE)
