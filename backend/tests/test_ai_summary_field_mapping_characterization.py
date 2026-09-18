"""
Bloco 3G — testes do mapeamento de campos de GET /api/v1/ai/summary
(backend/app/api/v1/routes/ai.py::summary / _rows_to_dicts).

Objetivo: documentar com evidência empírica o contrato CORRIGIDO de
serialização por transação. `_rows_to_dicts` (ai.py) monta cada item
de `txs` com:

    "descricao": getattr(r, "referencia", "") or "",
    "created_at": getattr(r, "criado_em", None)...

O model real `Transaction` (backend/app/models/transaction.py:8-18)
não tem colunas `descricao`/`created_at` -- tem `referencia`
(nullable) e `criado_em` (sempre preenchida, server_default=func.now())
em vez disso. As CHAVES do JSON ("descricao"/"created_at") continuam
as mesmas -- é o contrato já consumido pelo front -- só a ORIGEM do
dado mudou: agora reflete `referencia`/`criado_em` reais, em vez de
sempre "" / null.

Mudança intencional de contrato nesta revisão: antes, "descricao"
sempre saía "" e "created_at" sempre saía null, mesmo com
`referencia`/`criado_em` preenchidas. Agora refletem o dado real
(referencia None continua resultando em descricao "", já que
`referencia` é nullable no model). Não toca em `limit`, auth, formato
geral da resposta, frontend, nem em outros endpoints além de
GET /api/v1/ai/summary.

Auth/isolamento: mesmo padrão já usado em
test_ai_summary_auth_characterization.py -- TestClient real contra
app.main.app, com app.dependency_overrides para `get_db` (SQLite em
memória isolado, StaticPool, criado/destruído por teste; nunca
app.db). Identidade sempre via Depends(require_customer)/token Bearer
real (create_access_token canônico) -- nenhum bypass de auth.
"""
import os

os.environ.setdefault("SECRET_KEY", "ai-summary-field-mapping-characterization-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

from datetime import datetime

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


def _token_for(email: str) -> str:
    return create_access_token({"sub": email})


# ---------------------------------------------------------------------
# Contrato corrigido: a resposta mantém as chaves "descricao" e
# "created_at" no JSON de cada item de `txs`, e agora seus valores
# refletem `referencia`/`criado_em` reais.
# ---------------------------------------------------------------------
def test_descricao_and_created_at_reflect_real_referencia_and_criado_em(client, db_session):
    user = _create_user(db_session, "field-mapping-a@test.local")

    known_referencia = "Pagamento aluguel setembro"
    known_criado_em = datetime(2026, 3, 15, 12, 30, 0)

    tx = Transaction(
        user_id=user.id,
        tipo="recebimento",
        valor=1234.56,
        referencia=known_referencia,
        criado_em=known_criado_em,
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    # confere que o dado real foi de fato gravado como esperado --
    # se isso falhar, a prova abaixo não vale nada.
    assert tx.referencia == known_referencia
    assert tx.criado_em == known_criado_em

    token = _token_for(user.email)
    response = client.get(PATH, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_transacoes"] == 1

    item = body["txs"][0]

    # as chaves continuam presentes no contrato JSON (mesmas de sempre)...
    assert "descricao" in item
    assert "created_at" in item

    # ...e agora refletem o dado real: descricao é a referencia
    # gravada, created_at é a data real em ISO 8601.
    assert item["descricao"] == known_referencia, (
        "mudança intencional de contrato: 'descricao' agora reflete "
        "referencia real, em vez de sair sempre vazia"
    )

    assert item["created_at"] == known_criado_em.isoformat(), (
        "mudança intencional de contrato: 'created_at' agora reflete "
        "criado_em real em ISO 8601, em vez de sair sempre null"
    )


# ---------------------------------------------------------------------
# referencia ausente (nullable=True no model real): descricao continua
# "" -- getattr(r, "referencia", "") or "" trata None do mesmo jeito
# que ausência do atributo.
# ---------------------------------------------------------------------
def test_descricao_stays_blank_when_referencia_is_null(client, db_session):
    user = _create_user(db_session, "field-mapping-b@test.local")

    tx = Transaction(user_id=user.id, tipo="recebimento", valor=10.0, referencia=None)
    db_session.add(tx)
    db_session.commit()

    token = _token_for(user.email)
    response = client.get(PATH, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    item = response.json()["txs"][0]
    assert item["descricao"] == ""
