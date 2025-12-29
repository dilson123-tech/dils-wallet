from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.utils import hash_password
from app import models
import pytest

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # cria usuário de teste direto no banco
    if not db.query(models.User).filter(models.User.email == "test@local").first():
        db.add(models.User(
    email="test@local",
    username="test",
    hashed_password=hash_password("test123"),
    role="user"
))
        db.commit()
    db.close()
    yield

def test_login_and_balance_flow():
    resp = client.post("/api/v1/auth/login", json={"username": "test@local", "password": "test123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "tipo": "deposito",
        "valor": 123.45,
        "descricao": "pytest depósito",
        "referencia": "PYTEST-001",
    }
    r2 = client.post("/api/v1/transactions", json=payload, headers=headers)
    assert r2.status_code == 200
    body = r2.json()
    assert body["referencia"] == "PYTEST-001"

    r3 = client.get("/api/v1/transactions/balance", headers=headers)
    assert r3.status_code == 200
    assert "saldo" in r3.json()
