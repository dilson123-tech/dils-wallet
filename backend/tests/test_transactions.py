from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app import models
import pytest
from app.utils.security import hash_password

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # cria usuário de teste direto no banco
    u = db.query(models.User).filter(models.User.email == "test@local").first()
    if not u:
        u = models.User(
            username="test",
            email="test@local",
            hashed_password=hash_password("test123"),
            role="user",
        )
        db.add(u)
    else:
        u.hashed_password = hash_password("test123")
        if not getattr(u, "username", None):
            u.username = "test"
        if not getattr(u, "role", None):
            u.role = "user"
    db.commit()
    db.close()
    yield

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
