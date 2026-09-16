"""
Regressão de segurança: GET /api/v1/whoami
(backend/app/api/v1/routes/whoami.py::whoami) deve resolver o usuário
SEMPRE via Depends(require_customer) -- o mesmo pipeline canônico já
usado em GET /api/v1/users/me (app/utils/authz.py::get_current_user)
-- nunca mais interpretando um claim "sub" numérico como User.id cru.

Contexto (achado da auditoria JWT/AUTH PIPELINE): o endpoint tinha uma
pipeline de autenticação própria, com parsing manual de header e
segredo/algoritmo duplicados em app/auth.py. Uma divergência real (mas
não explorável sem o segredo de assinatura, já que nenhum emissor vivo
gera "sub" numérico) foi provada empiricamente: um token assinado
corretamente com sub = ID numérico de outro usuário era aceito por
whoami.py e rejeitado pelo pipeline canônico.

Esta correção troca a resolução de identidade para
Depends(require_customer), preservando o contrato JSON de resposta
(ok/user/claims/algo) -- o token ainda é decodificado uma segunda vez
dentro do endpoint apenas para ecoar "claims"/"algo", nunca para
decidir quem é o usuário.

Estratégia: TestClient real contra app.main.app, com
app.dependency_overrides apenas para get_db (SQLite em memória
isolado, StaticPool). Nenhum override de require_customer -- os tokens
usados são reais, assinados por app.utils.security.create_access_token
(a mesma função canônica de produção), para exercitar o pipeline de
ponta a ponta de verdade.

Nenhum acesso a rede externa, nenhum arquivo do repositório é tocado.
"""
import os

os.environ.setdefault("SECRET_KEY", "whoami-canonical-auth-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user_main import User
from app.utils.security import ALGORITHM, SECRET_KEY, create_access_token

WHOAMI_PATH = "/api/v1/whoami"
USERS_ME_PATH = "/api/v1/users/me"

_EXPECTED_TOP_KEYS = {"ok", "user", "claims", "algo"}
_EXPECTED_USER_KEYS = {"id", "email", "full_name", "type", "role"}


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


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------
# T1) Sem token -> 401.
# ---------------------------------------------------------------------
def test_t1_no_token_returns_401(client):
    response = client.get(WHOAMI_PATH)
    assert response.status_code == 401


# ---------------------------------------------------------------------
# T2) Token com sub = e-mail válido -> 200, resolve o usuário certo
# (regressão do caminho já funcional).
# ---------------------------------------------------------------------
def test_t2_valid_email_sub_resolves_correct_user(client, db_session):
    user = _create_user(db_session, "user-a@test.local")
    token = create_access_token({"sub": user.email})

    response = client.get(WHOAMI_PATH, headers=_bearer(token))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["user"]["id"] == user.id
    assert body["user"]["email"] == user.email


# ---------------------------------------------------------------------
# T3) Token com sub NUMÉRICO apontando para o id de OUTRO usuário --
# antes da correção isso era aceito (200, resolvia o outro usuário via
# User.id cru); agora deve ser rejeitado (401), igual ao pipeline
# canônico -- esta é a prova de que a divergência foi eliminada.
# ---------------------------------------------------------------------
def test_t3_numeric_sub_pointing_to_another_user_is_now_rejected(client, db_session):
    _create_user(db_session, "user-a@test.local")
    user_b = _create_user(db_session, "user-b@test.local")

    # token assinado com o segredo real, mas com sub = ID numérico de
    # user_b em vez do e-mail -- exatamente o payload que provava a
    # divergência na investigação anterior.
    forged_token = jwt.encode({"sub": str(user_b.id)}, SECRET_KEY, algorithm=ALGORITHM)

    response = client.get(WHOAMI_PATH, headers=_bearer(forged_token))

    assert response.status_code == 401


# ---------------------------------------------------------------------
# T4) Token com secret errado ou expirado -> 401 (regressão).
# ---------------------------------------------------------------------
def test_t4_wrong_secret_token_is_rejected(client, db_session):
    user = _create_user(db_session, "user-wrong-secret@test.local")
    bad_token = jwt.encode({"sub": user.email}, "definitely-not-the-real-secret", algorithm=ALGORITHM)

    response = client.get(WHOAMI_PATH, headers=_bearer(bad_token))

    assert response.status_code == 401


def test_t4_expired_token_is_rejected(client, db_session):
    user = _create_user(db_session, "user-expired@test.local")
    expired_token = create_access_token(
        {"sub": user.email}, expires_delta=timedelta(seconds=-10)
    )

    response = client.get(WHOAMI_PATH, headers=_bearer(expired_token))

    assert response.status_code == 401


# ---------------------------------------------------------------------
# T5) Contrato JSON preservado (ok/user/claims/algo) no caminho feliz.
# ---------------------------------------------------------------------
def test_t5_json_contract_is_preserved(client, db_session):
    user = _create_user(db_session, "user-contract@test.local")
    token = create_access_token({"sub": user.email})

    response = client.get(WHOAMI_PATH, headers=_bearer(token))

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == _EXPECTED_TOP_KEYS
    assert set(body["user"].keys()) == _EXPECTED_USER_KEYS
    assert body["algo"] == ALGORITHM
    assert body["claims"].get("sub") == user.email
    assert "exp" not in body["claims"]
    assert "iat" not in body["claims"]


# ---------------------------------------------------------------------
# T6) O mesmo token, consultado em /whoami e em /users/me, resolve ao
# mesmo usuário -- prova de que ambos os endpoints agora convergem
# para o mesmo pipeline canônico.
# ---------------------------------------------------------------------
def test_t6_whoami_and_users_me_agree_on_the_same_user_for_the_same_token(client, db_session):
    user = _create_user(db_session, "user-parity@test.local")
    token = create_access_token({"sub": user.email})

    whoami_response = client.get(WHOAMI_PATH, headers=_bearer(token))
    users_me_response = client.get(USERS_ME_PATH, headers=_bearer(token))

    assert whoami_response.status_code == 200
    assert users_me_response.status_code == 200
    assert whoami_response.json()["user"]["id"] == users_me_response.json()["id"]
    assert whoami_response.json()["user"]["email"] == users_me_response.json()["email"]
