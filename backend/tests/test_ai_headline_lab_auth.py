"""
Missão #8 — testes de autenticação de POST /api/v1/ai/headline e
POST /api/v1/ai/headline-lab
(backend/app/api/v1/routes/ai_chat.py::ia_headline_lab).

Mudança intencional de contrato: as duas rotas passaram a exigir
Depends(require_customer) (mesmo mecanismo de /chat, /summary e
/ai/pix-insight). Sem Authorization, com Authorization inválido ou
expirado, ou com token de um usuário inexistente, respondem 401.
X-User-Email nunca concede acesso nem altera a resposta.

O conteúdo continua LAB: com token válido a resposta é exatamente a
mesma de antes (números de exemplo fixos), sem nenhum dado real do
usuário autenticado. A cobertura de rate limit autenticado dessas
rotas vive em tests/test_ai_rate_limit.py.

Mesmo padrão de test_ai_chat_live_auth_characterization.py (F3):
TestClient in-process, app.dependency_overrides para get_db com SQLite
em memória (StaticPool, nunca backend/app.db) e guard de rede.
"""
import os
import socket
from datetime import timedelta
from decimal import Decimal

os.environ.setdefault("SECRET_KEY", "ai-headline-lab-auth-test-secret")
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

PATHS = ["/api/v1/ai/headline", "/api/v1/ai/headline-lab"]

EMAIL_A = "headline-auth-a@test.local"
EMAIL_B = "headline-auth-b@test.local"

# Contrato atual da resposta (inalterado pela Missão #8).
EXPECTED_RESPONSE = {
    "nivel": "ok",
    "headline": "Aurea Gold – Headline LAB funcionando",
    "subheadline": "Simulação de crédito inteligente com IA 3.0 em ambiente LAB.",
    "resumo": "Endpoint /api/v1/ai/headline-lab respondeu com sucesso em ambiente LAB.",
    "destaques": [
        "Status do Painel 3 operacional (LAB)",
        "Integração backend → IA 3.0 ok",
        "Pronto para ligar com dados reais depois",
    ],
    "recomendacao": "Agora é só conectar o Painel 3 e depois evoluir a lógica da IA.",
    "saldo_atual": 1280.0,
    "entradas_mes": 4500.0,
    "saidas_mes": 4230.0,
    "entradas_7d": 4500.0,
    "saidas_7d": 4230.0,
    "total_contas_7d": 980.0,
    "qtd_contas_7d": 3,
    "entradas_previstas": 0.0,
}


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
    """Qualquer conexão de socket falha o teste."""

    def _blocked(*args, **kwargs):
        raise AssertionError("conexão de rede inesperada durante /ai/headline")

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


def _token_for(email: str) -> str:
    return create_access_token({"sub": email})


@pytest.fixture()
def two_users(db_session):
    user_a = _create_user(db_session, EMAIL_A)
    user_b = _create_user(db_session, EMAIL_B)
    db_session.add(PixLedger(user_id=user_a.id, kind="credit", amount=Decimal("777.77")))
    db_session.add(PixLedger(user_id=user_b.id, kind="credit", amount=Decimal("888.88")))
    db_session.commit()
    return user_a, user_b


# A) Sem Authorization: 401.
@pytest.mark.parametrize("path", PATHS)
def test_no_authorization_returns_401(client, two_users, path):
    r = client.post(path)
    assert r.status_code == 401, r.text


# B) Access token válido: 200.
@pytest.mark.parametrize("path", PATHS)
def test_valid_access_token_returns_200(client, two_users, path):
    r = client.post(path, headers={"Authorization": f"Bearer {_token_for(EMAIL_A)}"})
    assert r.status_code == 200, r.text


# C) Access token inválido, expirado, ou de usuário inexistente: 401.
@pytest.mark.parametrize("path", PATHS)
def test_invalid_access_token_returns_401(client, two_users, path):
    r = client.post(path, headers={"Authorization": "Bearer not-a-real-jwt-token"})
    assert r.status_code == 401, r.text


@pytest.mark.parametrize("path", PATHS)
def test_expired_access_token_returns_401(client, two_users, path):
    expired = create_access_token({"sub": EMAIL_A}, expires_delta=timedelta(minutes=-5))
    r = client.post(path, headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401, r.text


@pytest.mark.parametrize("path", PATHS)
def test_token_for_unknown_user_returns_401(client, two_users, path):
    r = client.post(
        path,
        headers={"Authorization": f"Bearer {_token_for('ghost@test.local')}"},
    )
    assert r.status_code == 401, r.text


# D) X-User-Email arbitrário não concede acesso: sozinho, ou junto de
# um token inválido, continua 401 -- mesmo apontando para um usuário
# real do banco.
@pytest.mark.parametrize("path", PATHS)
def test_x_user_email_alone_does_not_grant_access(client, two_users, path):
    for email in (EMAIL_A, EMAIL_B, "attacker@evil.test"):
        r = client.post(path, headers={"X-User-Email": email})
        assert r.status_code == 401, (email, r.text)


@pytest.mark.parametrize("path", PATHS)
def test_x_user_email_with_invalid_token_does_not_grant_access(client, two_users, path):
    r = client.post(
        path,
        headers={"Authorization": "Bearer not-a-real-jwt-token", "X-User-Email": EMAIL_A},
    )
    assert r.status_code == 401, r.text


# D2) Com token válido, X-User-Email de outro usuário não muda nada na
# resposta.
@pytest.mark.parametrize("path", PATHS)
def test_x_user_email_has_no_effect_on_authenticated_response(client, two_users, path):
    auth = {"Authorization": f"Bearer {_token_for(EMAIL_A)}"}
    plain = client.post(path, headers=auth)
    spoofed = client.post(path, headers={**auth, "X-User-Email": EMAIL_B})

    assert plain.status_code == 200, plain.text
    assert spoofed.status_code == 200, spoofed.text
    assert spoofed.json() == plain.json()


# F) O contrato da resposta continua exatamente o mesmo.
@pytest.mark.parametrize("path", PATHS)
def test_response_contract_unchanged(client, two_users, path):
    r = client.post(path, headers={"Authorization": f"Bearer {_token_for(EMAIL_A)}"})
    assert r.status_code == 200, r.text
    assert r.json() == EXPECTED_RESPONSE


# G) Nenhum dado real do usuário é exposto: mesmo com ledger real
# (A=777,77 / B=888,88), a resposta é idêntica para A e B, igual ao
# contrato LAB fixo, e não contém e-mail, id nem valores reais.
@pytest.mark.parametrize("path", PATHS)
def test_no_real_user_data_is_exposed(client, two_users, path):
    user_a, user_b = two_users
    r_a = client.post(path, headers={"Authorization": f"Bearer {_token_for(EMAIL_A)}"})
    r_b = client.post(path, headers={"Authorization": f"Bearer {_token_for(EMAIL_B)}"})

    assert r_a.status_code == 200, r_a.text
    assert r_b.status_code == 200, r_b.text
    assert r_a.json() == r_b.json() == EXPECTED_RESPONSE

    for body in (r_a.text, r_b.text):
        for leaked in (EMAIL_A, EMAIL_B, "777", "888"):
            assert leaked not in body, leaked
        assert "user_id" not in body
        assert "email" not in body
