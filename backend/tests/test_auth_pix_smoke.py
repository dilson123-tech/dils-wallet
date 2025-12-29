import os
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

USER = os.getenv("AUREA_USER", "dilsonpereira231@gmail.com")
PASS = os.getenv("AUREA_PASS", "Aurea@12345")

def test_login_returns_token():
    r = client.post("/api/v1/auth/login", json={"username": USER, "password": PASS})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data and data["access_token"], data

def test_pix_balance_with_token_200():
    r = client.post("/api/v1/auth/login", json={"username": USER, "password": PASS})
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]

    r2 = client.get("/api/v1/pix/balance?days=7", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 200, r2.text
    j = r2.json()
    assert "saldo" in j
    assert "ultimos_7d" in j

def test_pix_balance_without_token_401():
    r = client.get("/api/v1/pix/balance?days=7")
    assert r.status_code in (401, 403), r.text
