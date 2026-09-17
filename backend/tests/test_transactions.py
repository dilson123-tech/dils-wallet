from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from app.database import Base, get_db
from app.main import app
from app import models
from app.utils.security import hash_password

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # SQLite em memória, descartável, isolado deste módulo -- nunca
    # backend/app.db. StaticPool garante uma única conexão compartilhada
    # entre todas as sessões abertas via get_db durante o módulo, então
    # dados de uma requisição (ex.: o usuário criado abaixo, ou o
    # refresh_token gravado pelo /login) ficam visíveis nas requisições
    # seguintes do mesmo teste.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db

    db = session_factory()
    try:
        # cria usuário de teste direto no banco descartável deste módulo
        db.add(
            models.User(
                username="test",
                email="test@local",
                hashed_password=hash_password("test123"),
                role="user",
            )
        )
        db.commit()
    finally:
        db.close()

    yield

    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_login_and_balance_flow():
    resp = client.post("/api/v1/auth/login", json={"username": "test@local", "password": "test123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # contrato real atual: PIX
    rbal = client.get("/api/v1/pix/balance?days=7", headers=headers)
    assert rbal.status_code == 200, rbal.text
    jbal = rbal.json()
    assert "saldo" in jbal
    assert "ultimos_7d" in jbal

    rh = client.get("/api/v1/pix/history", headers=headers)
    assert rh.status_code == 200, rh.text
    jh = rh.json()
    assert isinstance(jh, (list, dict)), type(jh)
