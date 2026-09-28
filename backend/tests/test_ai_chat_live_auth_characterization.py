"""
Bloco AI Chat auth — testes de CARACTERIZAÇÃO de
POST /api/v1/ai/chat (backend/app/api/v1/routes/ai_chat.py::ai_chat).

Objetivo: documentar com precisão o comportamento do endpoint agora
que ele usa Depends(require_customer) na borda (identidade sempre do
token Bearer autenticado, nunca de X-User-Email). Este arquivo NÃO
toca em chat_lab.py.

Mudança intencional de contrato: sem Authorization, com Authorization
expirado ou com Authorization inválido, o endpoint responde 401. Os
cenários com token válido continuam em 200, e um X-User-Email
conflitante nunca tem efeito sobre qual usuário é consultado.

F3: `/chat` deixou de fazer chamada HTTP interna para
http://127.0.0.1:8000. `_get_pix_balance`/`_get_pix_history` agora
consomem diretamente `pix.get_balance`/`pix.get_history` (in-process,
mesma sessão de banco, mesmo `current_user` autenticado). Por isso este
arquivo usa TestClient (ASGI in-process), sem subprocess, sem uvicorn e
sem depender da porta 8000 -- padrão já usado em
test_ai_summary_field_mapping_characterization.py: app.dependency_overrides
para `get_db` (SQLite em memória isolado, StaticPool, criado/destruído
por teste; nunca backend/app.db). Um guard de rede faz qualquer
tentativa de conexão de socket falhar o teste, provando que nenhum
servidor local é necessário.

Os cenários usam a intenção "histórico" do endpoint, cujo dado final
(soma de `valor` por tipo) reflete o dado consultado em PixLedger, fonte
de GET /api/v1/pix/history ("credit" -> "entrada", "debit" -> "saida").
"""
import os
import socket
from datetime import timedelta
from decimal import Decimal

os.environ.setdefault("SECRET_KEY", "ai-chat-live-auth-characterization-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import limiter
from app.database import Base, get_db
from app.main import app
from app.models.pix_ledger import PixLedger
from app.models.user_main import User
from app.utils.security import create_access_token

PATH = "/api/v1/ai/chat"
MSG_HISTORY = {"message": "qual é o meu histórico de pix"}
MSG_SALDO = {"message": "qual é o meu saldo"}

EMAIL_A = "chat-auth-a@test.local"
EMAIL_B = "chat-auth-b@test.local"


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
def no_network(monkeypatch):
    """Qualquer conexão de socket (ex.: 127.0.0.1:8000) falha o teste."""

    def _blocked(*args, **kwargs):
        raise AssertionError("conexão de rede inesperada durante /ai/chat")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


@pytest.fixture()
def client(db_session, no_network):
    def _override_get_db():
        yield db_session

    limiter.reset()
    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        limiter.reset()


def _create_user(db, email: str) -> User:
    user = User(email=email, hashed_password="x", role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _add_ledger(db, user: User, kind: str, amount: str) -> None:
    db.add(PixLedger(user_id=user.id, kind=kind, amount=Decimal(amount)))
    db.commit()


def _token_for(email: str) -> str:
    return create_access_token({"sub": email})


@pytest.fixture()
def two_users(db_session):
    user_a = _create_user(db_session, EMAIL_A)
    user_b = _create_user(db_session, EMAIL_B)
    _add_ledger(db_session, user_a, "credit", "111.00")
    _add_ledger(db_session, user_b, "credit", "222.00")
    return user_a, user_b


def _chat(client, headers, msg=MSG_HISTORY):
    r = client.post(PATH, json=msg, headers=headers)
    try:
        reply = r.json().get("reply", "")
    except Exception:
        reply = ""
    return r.status_code, reply


# ---------------------------------------------------------------------
# 1) Token do usuário A + X-User-Email do usuário B: a resposta nunca
# pode conter o dado real de B (R$ 222,00), só o de A (R$ 111,00).
# ---------------------------------------------------------------------
def test_token_a_with_x_user_email_b_never_returns_b_data(client, two_users):
    status, reply = _chat(
        client,
        {"Authorization": f"Bearer {_token_for(EMAIL_A)}", "X-User-Email": EMAIL_B},
    )

    assert status == 200
    assert "222,00" not in reply, "vazou o valor real do usuário B"
    assert "111,00" in reply, "esperava ver o valor real do próprio usuário A (dono do token)"


# ---------------------------------------------------------------------
# 2) Inverso: token do usuário B + X-User-Email do usuário A: a
# resposta nunca pode conter o dado real de A (R$ 111,00).
# ---------------------------------------------------------------------
def test_token_b_with_x_user_email_a_never_returns_a_data(client, two_users):
    status, reply = _chat(
        client,
        {"Authorization": f"Bearer {_token_for(EMAIL_B)}", "X-User-Email": EMAIL_A},
    )

    assert status == 200
    assert "111,00" not in reply, "vazou o valor real do usuário A"
    assert "222,00" in reply, "esperava ver o valor real do próprio usuário B (dono do token)"


# ---------------------------------------------------------------------
# 3) Sem Authorization: 401 (Depends(require_customer) rejeita antes de
# qualquer lógica de negócio rodar), sem nenhum dado real de PIX vazando.
# ---------------------------------------------------------------------
def test_no_authorization_returns_401(client, two_users):
    status, reply = _chat(client, {"X-User-Email": EMAIL_A})

    assert status == 401, (
        "mudança intencional de contrato: sem Authorization agora é 401, "
        "identidade nunca mais vem de X-User-Email"
    )
    assert "111,00" not in reply
    assert "222,00" not in reply


# ---------------------------------------------------------------------
# 4) Authorization inválido/expirado: 401, mesmo com X-User-Email de
# outro usuário mandado propositalmente -- sem vazamento de dado real.
# ---------------------------------------------------------------------
def test_expired_authorization_returns_401(client, two_users):
    expired_token = create_access_token({"sub": EMAIL_A}, expires_delta=timedelta(minutes=-5))
    status, reply = _chat(
        client,
        {"Authorization": f"Bearer {expired_token}", "X-User-Email": EMAIL_B},
    )

    assert status == 401, "mudança intencional de contrato: token expirado agora é 401"
    assert "111,00" not in reply
    assert "222,00" not in reply


def test_invalid_authorization_returns_401(client, two_users):
    status, reply = _chat(
        client,
        {"Authorization": "Bearer not-a-real-jwt-token", "X-User-Email": EMAIL_B},
    )

    assert status == 401, "mudança intencional de contrato: token inválido agora é 401"
    assert "111,00" not in reply
    assert "222,00" not in reply


# ---------------------------------------------------------------------
# 5) F3: débito no PixLedger vira "saida" em /pix/history e precisa ser
# somado como enviado (antes só "env" era reconhecido, então saídas
# reais apareciam como R$ 0,00).
# ---------------------------------------------------------------------
def test_history_counts_saida_as_enviado(client, db_session):
    user = _create_user(db_session, "chat-auth-debit@test.local")
    _add_ledger(db_session, user, "credit", "300.00")
    _add_ledger(db_session, user, "debit", "45.50")
    _add_ledger(db_session, user, "debit", "4.50")

    status, reply = _chat(client, {"Authorization": f"Bearer {_token_for(user.email)}"})

    assert status == 200
    assert "Total aproximado enviado: R$ 50,00" in reply
    assert "Total aproximado recebido: R$ 300,00" in reply


# ---------------------------------------------------------------------
# 6) F3: saldo real vem de pix.get_balance in-process (Ledger:
# créditos - débitos), com source "real", sem chamada HTTP interna.
# ---------------------------------------------------------------------
def test_saldo_uses_real_ledger_balance_in_process(client, db_session):
    user = _create_user(db_session, "chat-auth-saldo@test.local")
    _add_ledger(db_session, user, "credit", "300.00")
    _add_ledger(db_session, user, "debit", "45.50")

    status, reply = _chat(
        client,
        {"Authorization": f"Bearer {_token_for(user.email)}"},
        msg=MSG_SALDO,
    )

    assert status == 200
    assert "R$ 254,50" in reply
