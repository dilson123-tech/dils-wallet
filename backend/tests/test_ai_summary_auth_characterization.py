"""
Bloco 3F — testes de CARACTERIZAÇÃO (não de correção) de
GET /api/v1/ai/summary (backend/app/api/v1/routes/ai.py::summary).

Objetivo: documentar com evidência empírica o achado crítico da
auditoria pós-Bloco-3E: este endpoint não tem NENHUMA dependência de
autenticação (sem Depends(require_customer)/get_current_user), ignora
por completo tanto X-User-Email quanto Authorization, e devolve
transações de TODOS os usuários do banco sem filtro nenhum -- com o
parâmetro `limit` aceito sem teto superior no servidor. Este arquivo
NÃO altera nenhum código de produção e NÃO corrige nada.

Nota sobre o modelo (achado colateral, não corrigido aqui): a query
usa `PixTransaction` (app/models/pix_transaction.py), que é alias de
`Transaction` (app/models/transaction.py). As colunas reais desse
model são id, user_id, tipo, valor, criado_em -- NÃO existem
`descricao` nem `created_at`. `_rows_to_dicts` (ai.py) usa getattr com
defaults ("" e None) para esses dois campos inexistentes, então eles
sempre aparecem vazios/nulos na resposta, independente do que estiver
no banco. Por isso as provas de vazamento aqui usam `valor` e
`user_id` (colunas reais), nunca `descricao`.

Estratégia: TestClient real contra app.main.app, com
app.dependency_overrides só para `get_db` (SQLite em memória isolado,
StaticPool, criado/destruído por teste; nunca app.db real). Não existe
override de auth para aplicar -- é justamente o achado: o endpoint não
declara nenhuma dependência de autenticação para interceptar.
"""
import os

os.environ.setdefault("SECRET_KEY", "ai-summary-auth-characterization-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

from datetime import timedelta

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


def _create_user(db, email: str) -> User:
    user = User(email=email, hashed_password="x", role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_tx(db, *, user_id: int, tipo: str, valor: float) -> Transaction:
    tx = Transaction(user_id=user_id, tipo=tipo, valor=valor)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def _token_for(email: str) -> str:
    return create_access_token({"sub": email})


# ---------------------------------------------------------------------
# 1) Sem Authorization: contrato ATUAL é 200 (nada exigido), e o corpo
# já contém dado real de um usuário presente no banco.
# ---------------------------------------------------------------------
def test_no_authorization_current_contract_is_200_with_real_data(client, db_session):
    user_a = _create_user(db_session, "summary-a1@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=111.0)

    response = client.get(PATH)

    assert response.status_code == 200, (
        "contrato atual documentado é 200 sem Authorization; "
        "se isso mudou, é uma migração intencional de comportamento, não uma regressão deste teste"
    )
    body = response.json()
    assert body["total_transacoes"] == 1
    assert body["recebimentos"] == 111.0
    assert any(t["valor"] == 111.0 and t["user_id"] == user_a.id for t in body["txs"])


# ---------------------------------------------------------------------
# 2) Token do usuário A + X-User-Email do usuário B: nem o token nem o
# header selecionam ninguém -- a resposta contém as transações de
# AMBOS os usuários (prova de que a identidade é ignorada por completo).
# ---------------------------------------------------------------------
def test_token_a_with_x_user_email_b_returns_data_from_both_users(client, db_session):
    user_a = _create_user(db_session, "summary-a2@test.local")
    user_b = _create_user(db_session, "summary-b2@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=321.0)
    _create_tx(db_session, user_id=user_b.id, tipo="recebimento", valor=654.0)

    token_a = _token_for(user_a.email)
    response = client.get(
        PATH,
        headers={"Authorization": f"Bearer {token_a}", "X-User-Email": user_b.email},
    )

    assert response.status_code == 200
    body = response.json()
    valores = {t["valor"] for t in body["txs"]}
    user_ids = {t["user_id"] for t in body["txs"]}
    assert 321.0 in valores and 654.0 in valores, "esperava ver transações de AMBOS os usuários, sem filtro"
    assert user_a.id in user_ids and user_b.id in user_ids
    assert body["total_transacoes"] == 2


# ---------------------------------------------------------------------
# 3) Inverso: token do usuário B + X-User-Email do usuário A -- prova
# de que os headers de identidade não têm NENHUM efeito observável: o
# resultado é byte-a-byte idêntico ao de uma chamada sem headers.
# ---------------------------------------------------------------------
def test_token_b_with_x_user_email_a_returns_identical_result_to_no_headers(client, db_session):
    user_a = _create_user(db_session, "summary-a3@test.local")
    user_b = _create_user(db_session, "summary-b3@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=10.0)
    _create_tx(db_session, user_id=user_b.id, tipo="recebimento", valor=20.0)

    token_b = _token_for(user_b.email)

    resp_no_headers = client.get(PATH)
    resp_b_with_a_header = client.get(
        PATH,
        headers={"Authorization": f"Bearer {token_b}", "X-User-Email": user_a.email},
    )

    assert resp_no_headers.status_code == 200
    assert resp_b_with_a_header.status_code == 200
    assert resp_no_headers.json() == resp_b_with_a_header.json(), (
        "Authorization e X-User-Email não têm nenhum efeito observável na resposta -- "
        "é exatamente o mesmo resultado com ou sem eles"
    )


# ---------------------------------------------------------------------
# 4) Prova direta de vazamento cross-user: autenticado (token válido)
# como o usuário A, os dados reais do usuário B aparecem no corpo.
# ---------------------------------------------------------------------
def test_other_users_real_data_appears_in_response(client, db_session):
    user_a = _create_user(db_session, "summary-a4@test.local")
    user_b = _create_user(db_session, "summary-b4@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=999.99)
    _create_tx(db_session, user_id=user_b.id, tipo="envio", valor=777.77)

    token_a = _token_for(user_a.email)
    response = client.get(PATH, headers={"Authorization": f"Bearer {token_a}"})

    assert response.status_code == 200
    body = response.json()
    valores = {t["valor"] for t in body["txs"]}
    assert 777.77 in valores, "vazou o valor real de OUTRO usuário (B) para uma sessão autenticada como A"
    assert body["total_envios"] == 777.77  # tipo "envio" só existe no usuário B


# ---------------------------------------------------------------------
# 5) Token inválido / expirado: contrato ATUAL segue 200 com os MESMOS
# dados -- o token nunca é decodificado nem validado neste endpoint.
# ---------------------------------------------------------------------
def test_invalid_token_still_returns_200_with_same_data(client, db_session):
    user_a = _create_user(db_session, "summary-a5@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=55.0)

    baseline = client.get(PATH).json()
    resp_garbage = client.get(PATH, headers={"Authorization": "Bearer not-a-real-jwt-token"})

    assert resp_garbage.status_code == 200, "contrato atual documentado é 200 mesmo com token inválido"
    assert resp_garbage.json() == baseline


def test_expired_token_still_returns_200_with_same_data(client, db_session):
    user_a = _create_user(db_session, "summary-a6@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=66.0)

    baseline = client.get(PATH).json()
    expired = create_access_token({"sub": user_a.email}, expires_delta=timedelta(minutes=-5))
    resp_expired = client.get(PATH, headers={"Authorization": f"Bearer {expired}"})

    assert resp_expired.status_code == 200, "contrato atual documentado é 200 mesmo com token expirado"
    assert resp_expired.json() == baseline


# ---------------------------------------------------------------------
# 6) Parâmetro `limit`: sem teto superior no servidor. Os agregados
# (total_transacoes/total_envios/recebimentos/saldo_estimado) refletem
# até `limit` linhas de TODOS os usuários, mesmo quando a lista `txs`
# devolvida ao cliente é sempre cortada em 10 (txs[:10] em ai.py).
# ---------------------------------------------------------------------
def test_limit_default_is_50_but_returned_txs_list_is_capped_at_10(client, db_session):
    user_a = _create_user(db_session, "summary-limit-a@test.local")
    for i in range(15):
        _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=float(i + 1))

    response = client.get(PATH)

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 15, "agregado reflete as 15 linhas (dentro do default limit=50), não é limitado a 10"
    assert len(body["txs"]) == 10, "só a lista crua devolvida ao cliente é cortada em 10 (txs[:10])"


def test_limit_param_restricts_aggregate_row_count(client, db_session):
    user_a = _create_user(db_session, "summary-limit-b@test.local")
    for i in range(15):
        _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=float(i + 1))

    response = client.get(PATH, params={"limit": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 3, "limit=3 restringe os agregados às 3 transações mais recentes"


def test_limit_has_no_server_side_upper_bound(client, db_session):
    user_a = _create_user(db_session, "summary-limit-c@test.local")
    for i in range(20):
        _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=1.0)

    # limit muito acima do dataset real (20 linhas): o servidor aceita
    # sem erro, sem clamp e sem exigir nenhuma autorização adicional --
    # nada rejeita ou limita esse valor antes de chegar ao .limit() do SQL.
    response = client.get(PATH, params={"limit": 1_000_000})

    assert response.status_code == 200, "nenhum teto de `limit` é aplicado pelo servidor"
    body = response.json()
    assert body["total_transacoes"] == 20  # não estourou; só não havia mais linhas no banco
