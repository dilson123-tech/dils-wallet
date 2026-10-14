"""
P0.1 — bloqueio fail-closed de POST /api/v1/pix/send e
POST /api/v1/pix/send/intent enquanto não existe payout real.

Sem PIX_SEND_ENABLED="true" (ausente, vazio, "false" ou qualquer outro
valor), as duas rotas respondem 503 {"code": "PIX_SEND_DISABLED"} antes
de qualquer escrita: nenhuma Transaction, PixLedger, IdempotencyKey ou
PixSendIntent é criada e o saldo fica exatamente igual. Auth continua
vindo antes do bloqueio (sem token => 401).

Mesmo padrão de test_pix_descricao_max_length.py: TestClient contra
app.main.app, override apenas de get_db (SQLite em memória, StaticPool).
"""
import os

os.environ.setdefault("SECRET_KEY", "pix-send-disabled-gate-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import limiter
from app.database import Base, get_db
from app.main import app
from app.models.idempotency import IdempotencyKey
from app.models.pix_ledger import PixLedger
from app.models.pix_send_intent import PixSendIntent
from app.models.transaction import Transaction
from app.models.user_main import User
from app.utils.security import create_access_token

SEND_PATH = "/api/v1/pix/send"
INTENT_PATH = "/api/v1/pix/send/intent"
PATHS = [SEND_PATH, INTENT_PATH]

CUSTOMER_EMAIL = "pix-send-disabled-gate@test.local"
OTHER_EMAIL = "pix-send-disabled-gate-other@test.local"
SALDO_INICIAL = Decimal("100.00")

BODY = {"chave_pix": "dest@aurea.gold", "valor": "10.00", "descricao": "teste"}
EXPECTED_BLOCKED = {"code": "PIX_SEND_DISABLED", "detail": "Envio de PIX indisponível."}

# Qualquer valor diferente de "true" mantém bloqueado.
NON_ENABLING_VALUES = ["false", "False", "", " ", "0", "1", "yes", "on", "enabled", "truee", "t"]


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    limiter.reset()
    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        limiter.reset()


@pytest.fixture()
def customer(db_session):
    user = User(email=CUSTOMER_EMAIL, hashed_password="x", role="customer")
    other = User(email=OTHER_EMAIL, hashed_password="x", role="customer")
    db_session.add_all([user, other])
    db_session.commit()
    db_session.refresh(user)
    db_session.add(PixLedger(user_id=user.id, kind="credit", amount=SALDO_INICIAL))
    db_session.commit()
    return user


def _auth(extra: dict | None = None) -> dict:
    headers = {"Authorization": f"Bearer {create_access_token({'sub': CUSTOMER_EMAIL})}"}
    if extra:
        headers.update(extra)
    return headers


def _counts(db) -> dict:
    return {
        "transactions": db.query(Transaction).count(),
        "ledger": db.query(PixLedger).count(),
        "idempotency_keys": db.query(IdempotencyKey).count(),
        "intents": db.query(PixSendIntent).count(),
    }


def _saldo(db, user_id: int) -> Decimal:
    saldo = Decimal("0")
    for row in db.query(PixLedger).filter(PixLedger.user_id == user_id).all():
        amount = Decimal(str(row.amount))
        saldo += amount if row.kind == "credit" else -amount
    return saldo


def _assert_blocked(response):
    assert response.status_code == 503, response.text
    assert response.json() == EXPECTED_BLOCKED


# A) Flag ausente => bloqueado, sem nenhuma escrita (C/D/E).
@pytest.mark.parametrize("path", PATHS)
def test_flag_absent_blocks_without_side_effects(client, db_session, customer, monkeypatch, path):
    monkeypatch.delenv("PIX_SEND_ENABLED", raising=False)
    before = _counts(db_session)

    response = client.post(path, json=BODY, headers=_auth({"Idempotency-Key": "k-absent"}))

    _assert_blocked(response)
    assert _counts(db_session) == before
    assert _saldo(db_session, customer.id) == SALDO_INICIAL


# B) Flag false (e qualquer valor que não seja "true") => bloqueado,
# sem nenhuma escrita (C/D/E).
@pytest.mark.parametrize("value", NON_ENABLING_VALUES)
@pytest.mark.parametrize("path", PATHS)
def test_flag_not_true_blocks_without_side_effects(client, db_session, customer, monkeypatch, path, value):
    monkeypatch.setenv("PIX_SEND_ENABLED", value)
    before = _counts(db_session)

    response = client.post(path, json=BODY, headers=_auth({"Idempotency-Key": f"k-{value!r}"}))

    _assert_blocked(response)
    assert _counts(db_session) == before
    assert _saldo(db_session, customer.id) == SALDO_INICIAL


# C/D) Fluxo completo bloqueado: intent e send repetidos não deixam
# nenhum rastro e o saldo fica exatamente igual.
def test_blocked_intent_then_send_leaves_no_state(client, db_session, customer, monkeypatch):
    monkeypatch.setenv("PIX_SEND_ENABLED", "false")
    before = _counts(db_session)

    for _ in range(3):
        _assert_blocked(client.post(INTENT_PATH, json=BODY, headers=_auth()))
        _assert_blocked(
            client.post(SEND_PATH, json=BODY, headers=_auth({"Idempotency-Key": "k-repeat"}))
        )

    assert _counts(db_session) == before
    assert _counts(db_session)["transactions"] == 0
    assert _counts(db_session)["idempotency_keys"] == 0
    assert _counts(db_session)["intents"] == 0
    assert db_session.query(PixLedger).filter(PixLedger.kind == "debit").count() == 0
    assert _saldo(db_session, customer.id) == SALDO_INICIAL


# G) Headers, corpo e Idempotency-Key variados não contornam o bloqueio.
BYPASS_HEADERS = [
    {},
    {"Idempotency-Key": "k-1"},
    {"Idempotency-Key": ""},
    {"Idempotency-Key": "x" * 200},
    {"X-User-Email": OTHER_EMAIL},
    {"X-PIX-Send-Enabled": "true"},
    {"PIX_SEND_ENABLED": "true"},
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Wallet-Mode": "demo"},
]
BYPASS_BODIES = [
    BODY,
    {**BODY, "valor": "0.01"},
    {**BODY, "descricao": None},
    {**BODY, "pix_send_enabled": True},
    {**BODY, "force_new": True},
]


@pytest.mark.parametrize("extra", BYPASS_HEADERS)
@pytest.mark.parametrize("path", PATHS)
def test_headers_do_not_bypass_block(client, db_session, customer, monkeypatch, path, extra):
    monkeypatch.delenv("PIX_SEND_ENABLED", raising=False)
    before = _counts(db_session)

    _assert_blocked(client.post(path, json=BODY, headers=_auth(extra)))

    assert _counts(db_session) == before
    assert _saldo(db_session, customer.id) == SALDO_INICIAL


@pytest.mark.parametrize("body", BYPASS_BODIES)
@pytest.mark.parametrize("path", PATHS)
def test_body_does_not_bypass_block(client, db_session, customer, monkeypatch, path, body):
    monkeypatch.delenv("PIX_SEND_ENABLED", raising=False)
    before = _counts(db_session)

    _assert_blocked(client.post(path, json=body, headers=_auth({"Idempotency-Key": "k-body"})))

    assert _counts(db_session) == before
    assert _saldo(db_session, customer.id) == SALDO_INICIAL


def test_query_string_does_not_bypass_block(client, db_session, customer, monkeypatch):
    monkeypatch.delenv("PIX_SEND_ENABLED", raising=False)
    before = _counts(db_session)

    for path in PATHS:
        _assert_blocked(
            client.post(f"{path}?PIX_SEND_ENABLED=true&enabled=1", json=BODY, headers=_auth())
        )

    assert _counts(db_session) == before


# Auth continua antes do bloqueio: sem token => 401, nunca 503.
@pytest.mark.parametrize("path", PATHS)
def test_unauthenticated_still_401_when_blocked(client, db_session, customer, monkeypatch, path):
    monkeypatch.delenv("PIX_SEND_ENABLED", raising=False)
    before = _counts(db_session)

    response = client.post(path, json=BODY, headers={"X-User-Email": CUSTOMER_EMAIL})

    assert response.status_code == 401, response.text
    assert _counts(db_session) == before


# F) Com PIX_SEND_ENABLED=true o fluxo existente (intent -> send) segue
# funcionando e debita normalmente.
@pytest.mark.parametrize("value", ["true", "TRUE", " True "])
def test_flag_true_keeps_existing_flow(client, db_session, customer, monkeypatch, value):
    monkeypatch.setenv("PIX_SEND_ENABLED", value)

    intent = client.post(INTENT_PATH, json=BODY, headers=_auth())
    assert intent.status_code == 200, intent.text
    send_key = intent.json()["send_key"]

    sent = client.post(SEND_PATH, json=BODY, headers=_auth({"Idempotency-Key": send_key}))
    assert sent.status_code == 200, sent.text
    assert sent.json()["status"] == "success"

    assert db_session.query(Transaction).count() == 1
    assert db_session.query(PixLedger).filter(PixLedger.kind == "debit").count() == 1
    assert _saldo(db_session, customer.id) == SALDO_INICIAL - Decimal(BODY["valor"])


# O bloqueio é lido a cada requisição: desligar a flag volta a bloquear
# imediatamente, sem novo débito.
def test_flag_is_read_per_request(client, db_session, customer, monkeypatch):
    monkeypatch.setenv("PIX_SEND_ENABLED", "true")
    sent = client.post(SEND_PATH, json=BODY, headers=_auth({"Idempotency-Key": "k-on"}))
    assert sent.status_code == 200, sent.text
    after_enabled = _counts(db_session)
    saldo_enabled = _saldo(db_session, customer.id)

    monkeypatch.setenv("PIX_SEND_ENABLED", "false")
    _assert_blocked(client.post(SEND_PATH, json=BODY, headers=_auth({"Idempotency-Key": "k-off"})))
    # Nem o replay da mesma chave já usada passa pelo bloqueio.
    _assert_blocked(client.post(SEND_PATH, json=BODY, headers=_auth({"Idempotency-Key": "k-on"})))

    assert _counts(db_session) == after_enabled
    assert _saldo(db_session, customer.id) == saldo_enabled
