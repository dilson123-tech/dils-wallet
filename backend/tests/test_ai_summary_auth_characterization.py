"""
Bloco 3F — testes de CARACTERIZAÇÃO de
GET /api/v1/ai/summary (backend/app/api/v1/routes/ai.py::summary).

Objetivo: documentar com evidência empírica o comportamento do
endpoint agora que ele usa Depends(require_customer) na borda
(identidade sempre do token Bearer autenticado, nunca de
X-User-Email) e filtra PixTransaction por
`PixTransaction.user_id == current_user.id`.

Mudança intencional de contrato nesta revisão: sem Authorization, com
Authorization expirado ou com Authorization inválido, o endpoint agora
responde 401 (antes respondia 200 e devolvia transações de TODOS os
usuários do banco, sem filtro nenhum). Com token válido, a resposta
agora reflete só os dados do dono do token -- um X-User-Email
conflitante nunca tem efeito (nem antes tinha efeito real, já que o
header sempre foi decorativo; a diferença é que agora existe filtro
de verdade por usuário em vez de nenhum filtro).

Dois achados da auditoria pós-Bloco-3E foram DELIBERADAMENTE deixados
de fora desta correção (fora de escopo deste commit):
- o parâmetro `limit` continua sem teto superior no servidor;
- `_rows_to_dicts` (ai.py) continua usando getattr com defaults para
  `descricao`/`created_at`, colunas que não existem no model real
  `Transaction` (que tem `referencia`/`criado_em`) -- esses dois
  campos continuam sempre vazios/nulos na resposta.
Os testes de `limit` abaixo foram só ajustados para autenticar (já que
o endpoint agora exige token), mas continuam provando a ausência de
teto -- isso não foi corrigido.

Estratégia: TestClient real contra app.main.app, com
app.dependency_overrides para `get_db` (SQLite em memória isolado,
StaticPool, criado/destruído por teste; nunca app.db real). Não há
override de `require_customer` -- os tokens são JWTs reais gerados via
`create_access_token`, exercitando o pipeline canônico completo
(app/utils/authz.py::get_current_user) exatamente como em produção.
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
# 1) Sem Authorization: contrato canônico agora é 401
# (Depends(require_customer) rejeita antes de qualquer query rodar).
# ---------------------------------------------------------------------
def test_no_authorization_returns_401(client, db_session):
    user_a = _create_user(db_session, "summary-a1@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=111.0)

    response = client.get(PATH)

    assert response.status_code == 401, (
        "mudança intencional de contrato: sem Authorization agora é 401, "
        "identidade nunca mais vem de X-User-Email nem de ausência de auth"
    )
    assert "txs" not in response.json()


# ---------------------------------------------------------------------
# 2) Token do usuário A + X-User-Email do usuário B: a resposta contém
# SOMENTE os dados de A (dono do token) -- X-User-Email conflitante
# nunca seleciona B.
# ---------------------------------------------------------------------
def test_token_a_with_x_user_email_b_returns_only_a_data(client, db_session):
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
    assert valores == {321.0}, "esperava ver só a transação do dono do token (A)"
    assert user_ids == {user_a.id}
    assert body["total_transacoes"] == 1


# ---------------------------------------------------------------------
# 3) Inverso: token do usuário B + X-User-Email do usuário A -- a
# resposta contém SOMENTE os dados de B, e é idêntica a uma chamada
# autenticada como B sem X-User-Email nenhum (prova de que o header
# continua sem nenhum efeito observável).
# ---------------------------------------------------------------------
def test_token_b_with_x_user_email_a_returns_only_b_data_header_has_no_effect(client, db_session):
    user_a = _create_user(db_session, "summary-a3@test.local")
    user_b = _create_user(db_session, "summary-b3@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=10.0)
    _create_tx(db_session, user_id=user_b.id, tipo="recebimento", valor=20.0)

    token_b = _token_for(user_b.email)

    resp_b_no_header = client.get(PATH, headers={"Authorization": f"Bearer {token_b}"})
    resp_b_with_a_header = client.get(
        PATH,
        headers={"Authorization": f"Bearer {token_b}", "X-User-Email": user_a.email},
    )

    assert resp_b_no_header.status_code == 200
    assert resp_b_with_a_header.status_code == 200
    assert resp_b_no_header.json() == resp_b_with_a_header.json(), (
        "X-User-Email não tem nenhum efeito observável na resposta quando autenticado -- "
        "é exatamente o mesmo resultado com ou sem o header"
    )
    valores = {t["valor"] for t in resp_b_with_a_header.json()["txs"]}
    assert valores == {20.0}, "esperava ver só a transação do dono do token (B), nunca a de A"


# ---------------------------------------------------------------------
# 4) Isolamento cross-user: autenticado (token válido) como o usuário
# A, os dados reais do usuário B NUNCA aparecem no corpo.
# ---------------------------------------------------------------------
def test_user_a_never_receives_user_b_data(client, db_session):
    user_a = _create_user(db_session, "summary-a4@test.local")
    user_b = _create_user(db_session, "summary-b4@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=999.99)
    _create_tx(db_session, user_id=user_b.id, tipo="envio", valor=777.77)

    token_a = _token_for(user_a.email)
    response = client.get(PATH, headers={"Authorization": f"Bearer {token_a}"})

    assert response.status_code == 200
    body = response.json()
    valores = {t["valor"] for t in body["txs"]}
    assert 777.77 not in valores, "NUNCA deve vazar o valor real de outro usuário (B) para uma sessão autenticada como A"
    assert valores == {999.99}
    assert body["total_envios"] == 0.0  # o único "envio" (777.77) é de B, não de A
    assert body["total_transacoes"] == 1


# ---------------------------------------------------------------------
# 5) Token inválido / expirado: contrato canônico agora é 401.
# ---------------------------------------------------------------------
def test_invalid_token_returns_401(client, db_session):
    user_a = _create_user(db_session, "summary-a5@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=55.0)

    response = client.get(PATH, headers={"Authorization": "Bearer not-a-real-jwt-token"})

    assert response.status_code == 401, "mudança intencional de contrato: token inválido agora é 401"


def test_expired_token_returns_401(client, db_session):
    user_a = _create_user(db_session, "summary-a6@test.local")
    _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=66.0)

    expired = create_access_token({"sub": user_a.email}, expires_delta=timedelta(minutes=-5))
    response = client.get(PATH, headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401, "mudança intencional de contrato: token expirado agora é 401"


# ---------------------------------------------------------------------
# 6) Parâmetro `limit`: NÃO corrigido nesta revisão -- continua sem
# teto superior no servidor. Os testes só passaram a autenticar (já
# que o endpoint agora exige token); o comportamento do `limit`
# permanece o mesmo de antes, agora escopado ao próprio usuário.
# ---------------------------------------------------------------------
def test_limit_default_is_50_but_returned_txs_list_is_capped_at_10(client, db_session):
    user_a = _create_user(db_session, "summary-limit-a@test.local")
    for i in range(15):
        _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=float(i + 1))

    token_a = _token_for(user_a.email)
    response = client.get(PATH, headers={"Authorization": f"Bearer {token_a}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 15, "agregado reflete as 15 linhas (dentro do default limit=50), não é limitado a 10"
    assert len(body["txs"]) == 10, "só a lista crua devolvida ao cliente é cortada em 10 (txs[:10])"


def test_limit_param_restricts_aggregate_row_count(client, db_session):
    user_a = _create_user(db_session, "summary-limit-b@test.local")
    for i in range(15):
        _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=float(i + 1))

    token_a = _token_for(user_a.email)
    response = client.get(PATH, headers={"Authorization": f"Bearer {token_a}"}, params={"limit": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 3, "limit=3 restringe os agregados às 3 transações mais recentes"


def test_limit_has_no_server_side_upper_bound(client, db_session):
    user_a = _create_user(db_session, "summary-limit-c@test.local")
    for i in range(20):
        _create_tx(db_session, user_id=user_a.id, tipo="recebimento", valor=1.0)

    token_a = _token_for(user_a.email)
    # limit muito acima do dataset real (20 linhas): o servidor aceita
    # sem erro, sem clamp -- nada rejeita ou limita esse valor antes de
    # chegar ao .limit() do SQL. Isso NÃO foi corrigido nesta revisão.
    response = client.get(PATH, headers={"Authorization": f"Bearer {token_a}"}, params={"limit": 1_000_000})

    assert response.status_code == 200, "nenhum teto de `limit` é aplicado pelo servidor"
    body = response.json()
    assert body["total_transacoes"] == 20  # não estourou; só não havia mais linhas do próprio usuário
