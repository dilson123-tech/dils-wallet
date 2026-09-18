"""
Bloco 3H — testes do clamp do parâmetro `limit` de
GET /api/v1/ai/summary (backend/app/api/v1/routes/ai.py::summary).

Objetivo: documentar com evidência empírica o contrato CORRIGIDO de
`limit`. `ai.py` agora aplica, antes de usar `limit` na query, o mesmo
padrão já usado 5x no próprio backend
(backend/app/api/v1/routes/pix.py:161 e
backend/app/api/v1/routes/wallet.py:271,1949,2098):

    safe_limit = max(1, min(int(limit or 50), 100))

Mudança intencional de contrato nesta revisão:
    - limit ausente        -> 50 (sem mudança -- já era o default)
    - limit=0               -> 50 (antes: 0 resultados)
    - limit negativo        -> 1  (antes: sem limite efetivo no SQLite,
                                    devolvia TODAS as transações do usuário)
    - limit entre 1 e 100   -> preservado como está (sem mudança)
    - limit > 100           -> clampado em 100 (antes: sem teto)

Este arquivo NÃO altera auth, o mapeamento de campos do Bloco 3G,
formato geral da resposta, agregados, o corte `txs[:10]`, frontend,
nem outros endpoints -- só o clamp de `limit`.

Auth/isolamento: mesmo padrão já usado em
test_ai_summary_auth_characterization.py e
test_ai_summary_field_mapping_characterization.py -- TestClient real
contra app.main.app, com app.dependency_overrides para `get_db`
(SQLite em memória isolado, StaticPool, criado/destruído por teste;
nunca app.db). Identidade sempre via Depends(require_customer)/token
Bearer real (create_access_token canônico) -- nenhum bypass de auth.
"""
import os

os.environ.setdefault("SECRET_KEY", "ai-summary-limit-characterization-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.transaction import Transaction
from app.models.user_main import User
from app.utils.security import create_access_token

PATH = "/api/v1/ai/summary"

# Dataset grande o suficiente para provar TODOS os casos pedidos,
# incluindo o clamp em 100 para valores bem acima disso (101 e
# 1_000_000).
TOTAL_TRANSACOES_REAIS = 150


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

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def authed_user_with_150_transactions(db_session):
    user = User(email="limit-probe@test.local", hashed_password="x", role="customer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    for i in range(TOTAL_TRANSACOES_REAIS):
        db_session.add(
            Transaction(user_id=user.id, tipo="recebimento", valor=float(i + 1), referencia=f"ref-{i}")
        )
    db_session.commit()

    token = create_access_token({"sub": user.email})
    return token


def _get(client, token, limit=None):
    params = {} if limit is None else {"limit": limit}
    return client.get(PATH, headers={"Authorization": f"Bearer {token}"}, params=params)


# ---------------------------------------------------------------------
# limit ausente -> default 50 (sem mudança em relação ao contrato
# anterior).
# ---------------------------------------------------------------------
def test_limit_absent_defaults_to_50(client, authed_user_with_150_transactions):
    response = _get(client, authed_user_with_150_transactions)

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 50


# ---------------------------------------------------------------------
# limit=0 -> mudança intencional de contrato: agora cai no default
# (50), em vez de zerar o resumo silenciosamente.
# ---------------------------------------------------------------------
def test_limit_zero_falls_back_to_default_50(client, authed_user_with_150_transactions):
    response = _get(client, authed_user_with_150_transactions, limit=0)

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 50, (
        "mudança intencional de contrato: limit=0 agora cai no default (50), "
        "em vez de devolver um resumo vazio"
    )


# ---------------------------------------------------------------------
# limit negativo -> mudança intencional de contrato: agora vira piso 1
# (uma única transação), em vez de devolver todas as transações reais
# (efeito colateral do SQLite tratar LIMIT negativo como "sem limite").
# ---------------------------------------------------------------------
def test_limit_negative_is_clamped_to_floor_1(client, authed_user_with_150_transactions):
    response = _get(client, authed_user_with_150_transactions, limit=-1)

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 1, (
        "mudança intencional de contrato: limit negativo agora vira piso 1, "
        f"em vez de devolver as {TOTAL_TRANSACOES_REAIS} transações reais"
    )


# ---------------------------------------------------------------------
# limit=1 -> 1 transação (sem mudança; dentro da faixa 1..100
# preservada).
# ---------------------------------------------------------------------
def test_limit_one_returns_one(client, authed_user_with_150_transactions):
    response = _get(client, authed_user_with_150_transactions, limit=1)

    assert response.status_code == 200
    assert response.json()["total_transacoes"] == 1


# ---------------------------------------------------------------------
# limit=50 -> até 50 (sem mudança; dentro da faixa 1..100 preservada).
# ---------------------------------------------------------------------
def test_limit_50_returns_up_to_50(client, authed_user_with_150_transactions):
    response = _get(client, authed_user_with_150_transactions, limit=50)

    assert response.status_code == 200
    assert response.json()["total_transacoes"] == 50


# ---------------------------------------------------------------------
# limit=100 -> até 100 (sem mudança; é exatamente o teto, então este
# valor de fronteira continua idêntico).
# ---------------------------------------------------------------------
def test_limit_100_returns_up_to_100(client, authed_user_with_150_transactions):
    response = _get(client, authed_user_with_150_transactions, limit=100)

    assert response.status_code == 200
    assert response.json()["total_transacoes"] == 100


# ---------------------------------------------------------------------
# limit=101 e limit=1_000_000 -> mudança intencional de contrato:
# ambos agora são clampados em 100, em vez de devolver mais que isso.
# ---------------------------------------------------------------------
def test_limit_101_is_clamped_to_100(client, authed_user_with_150_transactions):
    response = _get(client, authed_user_with_150_transactions, limit=101)

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 100, (
        "mudança intencional de contrato: limit=101 agora é clampado em 100"
    )


def test_limit_1_000_000_is_clamped_to_100(client, authed_user_with_150_transactions):
    response = _get(client, authed_user_with_150_transactions, limit=1_000_000)

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 100, (
        "mudança intencional de contrato: limit muito acima do dataset real "
        "agora é clampado em 100, em vez de devolver todas as transações reais"
    )
