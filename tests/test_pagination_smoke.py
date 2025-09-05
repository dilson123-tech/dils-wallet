import os, httpx, pytest

BASE = os.getenv("BASE", "http://127.0.0.1:8000")
U = os.getenv("U", "teste@dilswallet.com")
P = os.getenv("P", "123456")

def _login():
    with httpx.Client(timeout=5.0) as c:
        try:
            r = c.post(f"{BASE}/api/v1/auth/login",
                       headers={"Content-Type":"application/x-www-form-urlencoded"},
                       data={"username": U, "password": P})
        except Exception as e:
            pytest.skip(f"server off? {e}")
        assert r.status_code == 200, f"login falhou: {r.text}"
        token = r.json().get("access_token")
        assert token, "sem access_token"
        return token

def test_transactions_paged_smoke():
    token = _login()
    with httpx.Client(timeout=5.0, headers={"Authorization": f"Bearer {token}"}) as c:
        r = c.get(f"{BASE}/api/v1/transactions/paged?page=1&page_size=5")
        assert r.status_code == 200, r.text
        data = r.json()
        meta = data.get("meta") or {}
        items = data.get("items") or []
        assert "page" in meta and "page_size" in meta and "total" in meta and "total_pages" in meta, meta
        assert isinstance(items, list)
        assert len(items) <= meta.get("page_size", 5)
