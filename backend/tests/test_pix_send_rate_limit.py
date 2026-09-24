"""
Rate limit (SlowAPI, "10/minute" por IP+rota) das rotas de envio PIX:
  - POST /api/v1/pix/send
  - POST /api/v1/pix/send/intent
  - POST /api/v1/pix/send/intent/ack

Garantias cobertas:
  - cada rota bloqueia a 11ª requisição do mesmo cliente com 429;
  - os buckets são separados por rota (estourar /send não bloqueia
    /send/intent);
  - requisições sem autenticação (401) não consomem o limite, porque o
    limite é verificado depois das dependências da rota;
  - /send bloqueado ou rejeitado não produz efeito financeiro: nenhuma
    Transaction, nenhum IdempotencyKey, ledger inalterado.

Sem efeitos financeiros reais: /send é chamado SEM Idempotency-Key, que
send_pix() rejeita com 400 antes de qualquer escrita; /send/intent só
reserva intents; /send/intent/ack usa uma send_key inexistente (409).

Mesmo padrão de isolamento de test_pix_send_intent_http_contract.py:
subprocess Python isolado, com DATABASE_URL apontando para um SQLite
descartável num diretório temporário definido ANTES de importar
app.main — nunca toca backend/app.db nem ambientes remotos. O
subprocess também isola o estado global em memória do Limiter.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

_PROBE_SCRIPT = r"""
import json

from app.database import Base, engine, SessionLocal
from app.utils.security import hash_password
from app.models.user_main import User
from app.models.pix_ledger import PixLedger
from app.models.transaction import Transaction
from app.models.idempotency import IdempotencyKey
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)


def make_user(email):
    db = SessionLocal()
    user = User(email=email, hashed_password=hash_password("test123"), role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(PixLedger(user_id=user.id, kind="credit", amount=1000))
    db.commit()
    uid = user.id
    db.close()
    return uid


def login(client, email):
    resp = client.post("/api/v1/auth/login", json={"username": email, "password": "test123"})
    assert resp.status_code == 200, ("login", resp.status_code, resp.text)
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def counts():
    db = SessionLocal()
    try:
        return {
            "ledger": db.query(PixLedger).count(),
            "transactions": db.query(Transaction).count(),
            "idempotency_keys": db.query(IdempotencyKey).count(),
        }
    finally:
        db.close()


client = TestClient(app)
make_user("pix-rl@test.local")
headers = login(client, "pix-rl@test.local")

payload = {"chave_pix": "dest-rl@aurea.gold", "valor": 1.00, "descricao": "RL"}
results = {}

# --- /send sem Idempotency-Key: 400 sem efeito, mas consome o limite ---
results["counts_before"] = counts()
results["send_statuses"] = [
    client.post("/api/v1/pix/send", json=payload, headers=headers).status_code
    for _ in range(11)
]
results["counts_after_send"] = counts()

# --- /send/intent: bucket próprio, primeira chamada passa ---
intent_payload = dict(payload, force_new=False)
results["intent_statuses"] = [
    client.post("/api/v1/pix/send/intent", json=intent_payload, headers=headers).status_code
    for _ in range(11)
]

# --- /send/intent/ack: 401 sem auth não consome; depois 10x409 e 429 ---
ack_body = {"send_key": "rl-nonexistent-send-key"}
results["ack_unauth_statuses"] = [
    client.post("/api/v1/pix/send/intent/ack", json=ack_body).status_code
    for _ in range(15)
]
results["ack_statuses"] = [
    client.post("/api/v1/pix/send/intent/ack", json=ack_body, headers=headers).status_code
    for _ in range(11)
]
results["counts_after_all"] = counts()

print(json.dumps(results))
"""


def _run_probe() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "pix-send-rate-limit-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"
        env["LOGIN_RL_ENABLED"] = "0"

        proc = subprocess.run(
            [sys.executable, "-c", _PROBE_SCRIPT],
            cwd=BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 0, (
            f"subprocess falhou:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
        return json.loads(proc.stdout.strip().splitlines()[-1])


_RESULTS = None


def _results() -> dict:
    global _RESULTS
    if _RESULTS is None:
        _RESULTS = _run_probe()
    return _RESULTS


def test_pix_send_blocks_11th_request_with_429():
    r = _results()
    assert r["send_statuses"] == [400] * 10 + [429]


def test_pix_send_rate_limited_requests_have_no_financial_effect():
    r = _results()
    expected = {"ledger": 1, "transactions": 0, "idempotency_keys": 0}
    assert r["counts_before"] == expected
    assert r["counts_after_send"] == expected
    assert r["counts_after_all"] == expected


def test_pix_send_intent_has_its_own_bucket_and_blocks_11th():
    r = _results()
    # 1ª chamada 200 logo após /send estourar prova que os buckets são por rota.
    assert r["intent_statuses"] == [200] * 10 + [429]


def test_pix_send_intent_ack_unauthenticated_does_not_consume_and_blocks_11th():
    r = _results()
    assert r["ack_unauth_statuses"] == [401] * 15
    assert r["ack_statuses"] == [409] * 10 + [429]
