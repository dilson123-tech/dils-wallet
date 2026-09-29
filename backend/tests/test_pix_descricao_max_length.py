"""
Pendência #15 do handoff: `descricao` de POST /api/v1/pix/send e
POST /api/v1/pix/send/intent agora tem max_length=255, o mesmo limite da
coluna PixLedger.description (String(255)). Antes, uma descrição maior
passava pelo schema e só falhava no commit do PostgreSQL (500). Agora é
rejeitada com 422 antes de qualquer efeito, nas duas rotas.

TestClient contra app.main.app, com override apenas de get_db (SQLite em
memória, StaticPool). Token de acesso real, assinado pela função de
produção.
"""
import os

os.environ.setdefault("SECRET_KEY", "pix-descricao-max-length-test-secret")
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
from app.services.pix_service import pix_send_request_hash, round_pix_money
from app.utils.security import create_access_token

SEND_PATH = "/api/v1/pix/send"
INTENT_PATH = "/api/v1/pix/send/intent"

CUSTOMER_EMAIL = "pix-descricao-max-length@test.local"
CHAVE_PIX = "dest@aurea.gold"
VALOR = "10.00"

DESCRICAO_255 = "d" * 255
DESCRICAO_256 = "d" * 256


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
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    db_session.add(PixLedger(user_id=user.id, kind="credit", amount=Decimal("100.00")))
    db_session.commit()
    return user


def _auth(extra: dict | None = None) -> dict:
    headers = {"Authorization": f"Bearer {create_access_token({'sub': CUSTOMER_EMAIL})}"}
    if extra:
        headers.update(extra)
    return headers


def _send_body(descricao) -> dict:
    return {"chave_pix": CHAVE_PIX, "valor": VALOR, "descricao": descricao}


def _counts(db) -> dict:
    return {
        "transactions": db.query(Transaction).count(),
        "debits": db.query(PixLedger).filter(PixLedger.kind == "debit").count(),
        "idempotency_keys": db.query(IdempotencyKey).count(),
        "intents": db.query(PixSendIntent).count(),
    }


def _fingerprint(user_id: int, descricao: str) -> str:
    return pix_send_request_hash(
        user_id=user_id,
        valor=round_pix_money(Decimal(VALOR)),
        chave_pix=CHAVE_PIX,
        descricao=descricao,
    )


def test_send_rejects_256_chars_with_422_and_no_side_effects(client, db_session, customer):
    before = _counts(db_session)

    response = client.post(
        SEND_PATH,
        json=_send_body(DESCRICAO_256),
        headers=_auth({"Idempotency-Key": "k-send-256"}),
    )

    assert response.status_code == 422
    assert _counts(db_session) == before


def test_intent_rejects_256_chars_with_422_and_no_side_effects(client, db_session, customer):
    before = _counts(db_session)

    response = client.post(INTENT_PATH, json=_send_body(DESCRICAO_256), headers=_auth())

    assert response.status_code == 422
    assert _counts(db_session) == before


def test_255_chars_intent_then_send_stay_consistent(client, db_session, customer):
    intent = client.post(INTENT_PATH, json=_send_body(DESCRICAO_255), headers=_auth())
    assert intent.status_code == 200
    intent_body = intent.json()
    assert intent_body["can_send"] is True
    send_key = intent_body["send_key"]

    stored_intent = db_session.query(PixSendIntent).one()
    assert stored_intent.fingerprint_hash == _fingerprint(customer.id, DESCRICAO_255)

    sent = client.post(
        SEND_PATH,
        json=_send_body(DESCRICAO_255),
        headers=_auth({"Idempotency-Key": send_key}),
    )
    assert sent.status_code == 200
    assert sent.json()["status"] == "success"

    debit = db_session.query(PixLedger).filter(PixLedger.kind == "debit").one()
    assert debit.description == DESCRICAO_255
    assert db_session.query(Transaction).count() == 1

    # Mesmo payload => mesmo hash entre intent e idempotência do envio.
    request_hashes = {row.request_hash for row in db_session.query(IdempotencyKey).all()}
    assert request_hashes == {stored_intent.fingerprint_hash}


@pytest.mark.parametrize("descricao", [None, ""])
def test_send_empty_or_none_descricao_still_uses_pix(client, db_session, customer, descricao):
    response = client.post(
        SEND_PATH,
        json=_send_body(descricao),
        headers=_auth({"Idempotency-Key": f"k-send-empty-{descricao!r}"}),
    )

    assert response.status_code == 200
    debit = db_session.query(PixLedger).filter(PixLedger.kind == "debit").one()
    assert debit.description == "PIX"


@pytest.mark.parametrize("descricao", [None, ""])
def test_intent_empty_or_none_descricao_still_uses_pix(client, db_session, customer, descricao):
    response = client.post(INTENT_PATH, json=_send_body(descricao), headers=_auth())

    assert response.status_code == 200
    stored_intent = db_session.query(PixSendIntent).one()
    assert stored_intent.fingerprint_hash == _fingerprint(customer.id, "PIX")
