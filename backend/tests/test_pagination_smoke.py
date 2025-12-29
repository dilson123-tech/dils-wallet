import os, httpx, pytest

BASE = os.getenv("BASE", "http://127.0.0.1:8000")
U = os.getenv("AUREA_USER", "dilsonpereira231@gmail.com")
P = os.getenv("AUREA_PASS", "Aurea@12345")

def _login():
    with httpx.Client(timeout=5.0) as c:
        try:
            r = c.post(f"{BASE}/api/v1/auth/login",
           json={"username": U, "password": P})
        except Exception as e:
            pytest.skip(f"server off? {e}")
        assert r.status_code == 200, r.text
        j = r.json()
        assert isinstance(j, (list, dict)), type(j)
        # aceita vazio em ambiente limpo, mas tem que ser JSON válido
        token = r.json().get("access_token")
        assert token, "sem access_token"
        return token

def test_transactions_paged_smoke():
    token = _login()
    with httpx.Client(timeout=5.0, headers={"Authorization": f"Bearer {token}"}) as c:
        r = c.get(f"{BASE}/api/v1/pix/history")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, (list, dict)), type(data)

