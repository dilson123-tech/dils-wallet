"""
Regressão de segurança: POST /api/v1/ai/ai/pix-insight
(backend/app/api/v1/routes/ai_chat.py::ia_pix_insight) deve resolver a
identidade do usuário SEMPRE via Depends(require_customer) -- nunca via
o header X-User-Email, que é livremente controlado pelo cliente.

Contexto (achado da auditoria JWT/AUTH PIPELINE): o endpoint estava
montado sem nenhuma dependência de autenticação e resolvia o usuário
consultado por um `db.query(User).filter(User.email == x_user_email)`
direto -- um IDOR não-autenticado por desenho. Na prática ele já
retornava 500 antes de vazar qualquer dado, por um NameError
pré-existente (`SessionLocal`/`Session`/`User`/`PixTransaction`/
`datetime`/`timedelta` nunca importados no escopo do módulo) -- ou
seja, o risco era real por desenho, mas inerte por acidente.

Esta correção adiciona `Depends(require_customer)` + `Depends(get_db)`
(mesmo padrão já usado em app/api/v1/routes/pix.py::get_balance) e
troca a fonte de identidade para `current_user.id`, sem alterar o
contrato JSON de resposta. Também corrige um segundo bug independente
descoberto durante a implementação: o código usava
`PixTransaction.timestamp`/`tx.taxa_valor`, campos que não existem no
model real `app.models.transaction.Transaction` (só existe
`criado_em`; `taxa_valor` nunca existiu) -- sem essa correção a query
nem chegaria a ser construída, mesmo já autenticado.

Estratégia: TestClient real contra app.main.app, com
app.dependency_overrides para `get_db` (SQLite em memória isolado,
StaticPool, criado/destruído por teste) e para `require_customer`
(simula "autenticado como o usuário X" sem precisar emitir JWT real).
Quando o teste precisa provar o caminho SEM token (T1), nenhum
override de `require_customer` é aplicado -- a dependência real roda e
rejeita por falta de header Authorization, exatamente como em
produção.

Nenhum acesso a rede externa, nenhum arquivo do repositório é tocado
(app.db real nunca é usado -- get_db é sempre substituído antes de
qualquer request).
"""
import os

os.environ.setdefault("SECRET_KEY", "ai-chat-pix-insight-test-secret")
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
from app.utils.authz import require_customer

PATH = "/api/v1/ai/ai/pix-insight"

_EXPECTED_METRICAS_KEYS = {
    "total_transacoes",
    "entradas_brutas",
    "saidas_brutas",
    "taxas_totais",
    "saldo_liquido_estimado",
    "entradas_7d",
    "saidas_7d",
    "entradas_mes",
    "saidas_mes",
}
_EXPECTED_TOP_KEYS = {"nivel", "headline", "subheadline", "resumo", "metricas"}


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
        app.dependency_overrides.pop(require_customer, None)


def _create_user(db, email: str) -> User:
    user = User(email=email, hashed_password="x", role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_tx(db, *, user_id: int, tipo: str, valor: float) -> None:
    db.add(Transaction(user_id=user_id, tipo=tipo, valor=valor))
    db.commit()


def _auth_as(user: User) -> None:
    app.dependency_overrides[require_customer] = lambda: user


# ---------------------------------------------------------------------
# T1) Sem token -> 401, nenhuma query ao banco é feita.
# ---------------------------------------------------------------------
def test_t1_no_token_returns_401_and_never_queries_db(client, db_session, monkeypatch):
    original_query = db_session.query
    calls = []

    def _spy_query(*args, **kwargs):
        calls.append((args, kwargs))
        return original_query(*args, **kwargs)

    monkeypatch.setattr(db_session, "query", _spy_query)

    response = client.post(PATH)

    assert response.status_code == 401
    assert calls == [], "nenhuma query deveria ter sido feita antes da autenticação"


# ---------------------------------------------------------------------
# T2) Header X-User-Email mentiroso não seleciona o usuário -- a
# resposta reflete sempre o dono do token (current_user), nunca o
# e-mail informado no header.
# ---------------------------------------------------------------------
def test_t2_lying_x_user_email_header_never_selects_another_user(client, db_session):
    user_a = _create_user(db_session, "user-a@test.local")
    user_b = _create_user(db_session, "user-b@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=100.0)
    _create_tx(db_session, user_id=user_b.id, tipo="recebimento", valor=999.0)

    _auth_as(user_a)
    response = client.post(PATH, headers={"X-User-Email": user_b.email})

    assert response.status_code == 200
    metricas = response.json()["metricas"]
    assert metricas["total_transacoes"] == 1
    assert metricas["entradas_brutas"] == 100.0
    assert metricas["entradas_brutas"] != 999.0


# ---------------------------------------------------------------------
# T3) Header ausente produz exatamente o mesmo resultado de T2 --
# prova que o header é decorativo, nunca fonte de identidade.
# ---------------------------------------------------------------------
def test_t3_missing_x_user_email_header_yields_identical_result_to_t2(client, db_session):
    user_a = _create_user(db_session, "user-a@test.local")
    user_b = _create_user(db_session, "user-b@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=100.0)
    _create_tx(db_session, user_id=user_b.id, tipo="recebimento", valor=999.0)

    _auth_as(user_a)
    response = client.post(PATH)  # sem X-User-Email

    assert response.status_code == 200
    metricas = response.json()["metricas"]
    assert metricas["total_transacoes"] == 1
    assert metricas["entradas_brutas"] == 100.0


# ---------------------------------------------------------------------
# T4) Isolamento cruzado nas duas direções, com valores distintos por
# usuário -- cada chamada autenticada só enxerga os próprios dados.
# ---------------------------------------------------------------------
def test_t4_cross_user_isolation_both_directions(client, db_session):
    user_a = _create_user(db_session, "user-a@test.local")
    user_b = _create_user(db_session, "user-b@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=100.0)
    _create_tx(db_session, user_id=user_a.id, tipo="envio", valor=40.0)
    _create_tx(db_session, user_id=user_b.id, tipo="recebimento", valor=500.0)
    _create_tx(db_session, user_id=user_b.id, tipo="envio", valor=10.0)

    _auth_as(user_a)
    resp_a = client.post(PATH)
    assert resp_a.status_code == 200
    metricas_a = resp_a.json()["metricas"]
    assert metricas_a["total_transacoes"] == 2
    assert metricas_a["entradas_brutas"] == 100.0
    assert metricas_a["saidas_brutas"] == 40.0

    _auth_as(user_b)
    resp_b = client.post(PATH)
    assert resp_b.status_code == 200
    metricas_b = resp_b.json()["metricas"]
    assert metricas_b["total_transacoes"] == 2
    assert metricas_b["entradas_brutas"] == 500.0
    assert metricas_b["saidas_brutas"] == 10.0


# ---------------------------------------------------------------------
# T5) Usuário autenticado sem transações -> nivel "vazio" e métricas
# zeradas, mesmo havendo dados de OUTROS usuários no mesmo banco.
# ---------------------------------------------------------------------
def test_t5_authenticated_user_without_transactions_gets_zeroed_response(client, db_session):
    user_with_data = _create_user(db_session, "has-data@test.local")
    user_without_data = _create_user(db_session, "no-data@test.local")
    _create_tx(db_session, user_id=user_with_data.id, tipo="recebimento", valor=250.0)

    _auth_as(user_without_data)
    response = client.post(PATH)

    assert response.status_code == 200
    body = response.json()
    assert body["nivel"] == "vazio"
    metricas = body["metricas"]
    assert metricas["total_transacoes"] == 0
    assert metricas["entradas_brutas"] == 0.0
    assert metricas["saidas_brutas"] == 0.0


# ---------------------------------------------------------------------
# T6) Regressão do NameError/AttributeError pré-existentes: uma
# chamada autenticada e válida nunca retorna 500.
# ---------------------------------------------------------------------
def test_t6_authenticated_call_never_returns_500(client, db_session):
    user = _create_user(db_session, "regression@test.local")
    _create_tx(db_session, user_id=user.id, tipo="recebimento", valor=10.0)

    _auth_as(user)
    response = client.post(PATH)

    assert response.status_code == 200, response.text
    assert response.status_code != 500


# ---------------------------------------------------------------------
# T7) Contrato JSON preservado: mesmas chaves de nível superior e de
# "metricas" de antes da correção.
# ---------------------------------------------------------------------
def test_t7_json_contract_keys_are_preserved(client, db_session):
    user = _create_user(db_session, "contract@test.local")
    _create_tx(db_session, user_id=user.id, tipo="recebimento", valor=10.0)

    _auth_as(user)
    response = client.post(PATH)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == _EXPECTED_TOP_KEYS
    assert set(body["metricas"].keys()) == _EXPECTED_METRICAS_KEYS

    # também no caminho "vazio" (sem transações), o contrato é o mesmo.
    empty_user = _create_user(db_session, "contract-empty@test.local")
    _auth_as(empty_user)
    response_empty = client.post(PATH)
    assert response_empty.status_code == 200
    body_empty = response_empty.json()
    assert set(body_empty.keys()) == _EXPECTED_TOP_KEYS
    assert set(body_empty["metricas"].keys()) == _EXPECTED_METRICAS_KEYS
