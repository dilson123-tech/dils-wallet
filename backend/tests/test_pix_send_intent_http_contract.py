"""
M2 — validação de contrato HTTP real (FastAPI TestClient) do fluxo de
intent de PIX, provando que as rotas efetivamente montadas em app.main
correspondem exatamente ao contrato consumido pelo frontend
(aurea-gold-client/src/lib/pixIntentManager.ts).

Mesmo padrão de isolamento de test_dev_seed_router_gate.py: subprocess
Python isolado, com DATABASE_URL apontando para um arquivo SQLite
descartável num diretório temporário definido ANTES de importar
app.main — nunca toca backend/app.db. Reutiliza a infraestrutura
TestClient já usada em 6 outros arquivos deste diretório; nenhuma nova
infraestrutura de teste é introduzida.

Não repete os testes de concorrência PostgreSQL (já provados em
test_pix_send_intent_concurrency_postgres.py) — este arquivo prova a
camada HTTP/contrato, não concorrência.
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
from app.models.pix_send_intent import PixSendIntent
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


client = TestClient(app)
real_user_id = make_user("intent-contract@test.local")
headers = login(client, "intent-contract@test.local")

results = {}

# --- A) reserva inicial, com campo extra "user_id"/"ownerId" injetado no
# body, que NUNCA deve ser honrado (auth/isolation: sempre current_user.id).
# Mesmo payload (chave_pix/valor/descricao) usado depois em B, C, D, E —
# reserve e send precisam receber exatamente os mesmos dados. ---
payload_a = {
    "chave_pix": "dest-a@aurea.gold",
    "valor": 12.34,
    "descricao": "Pagamento A",
    "force_new": False,
    "user_id": 999999,
    "ownerId": "someone-else",
}
r_a = client.post("/api/v1/pix/send/intent", json=payload_a, headers=headers)
results["a_status"] = r_a.status_code
results["a_body"] = r_a.json()

db = SessionLocal()
intent_row = db.query(PixSendIntent).filter_by(send_key=r_a.json().get("send_key")).first()
results["a_intent_owner_matches_authenticated_user"] = (
    intent_row is not None and intent_row.user_id == real_user_id
)
db.close()

k1 = r_a.json().get("send_key")

# --- B) envio real com K1, EXATAMENTE o mesmo chave_pix/valor/descricao
# usados na reserva (payload_a) ---
send_body = {"chave_pix": payload_a["chave_pix"], "valor": payload_a["valor"], "descricao": payload_a["descricao"]}
r_b = client.post(
    "/api/v1/pix/send",
    json=send_body,
    headers={**headers, "Idempotency-Key": k1},
)
results["b_status"] = r_b.status_code
results["b_body"] = r_b.json()

# --- C) ack ---
r_c = client.post("/api/v1/pix/send/intent/ack", json={"send_key": k1}, headers=headers)
results["c_status"] = r_c.status_code
results["c_body"] = r_c.json()

# --- D) mesma reserva normal depois do ack -> NÃO cria K2 ---
r_d = client.post("/api/v1/pix/send/intent", json=payload_a, headers=headers)
results["d_status"] = r_d.status_code
results["d_body"] = r_d.json()

# --- E) reserva explícita force_new=true -> cria K2 ---
payload_a_force = dict(payload_a)
payload_a_force["force_new"] = True
r_e = client.post("/api/v1/pix/send/intent", json=payload_a_force, headers=headers)
results["e_status"] = r_e.status_code
results["e_body"] = r_e.json()

# --- 3) pending + force_new=true -> 409, fail-closed, sem substituir K1 ---
payload_pending = {
    "chave_pix": "dest-pending@aurea.gold",
    "valor": 50.00,
    "descricao": "Pagamento pendente",
    "force_new": False,
}
r_pending_reserve = client.post("/api/v1/pix/send/intent", json=payload_pending, headers=headers)
k1_pending = r_pending_reserve.json().get("send_key")

payload_pending_force = dict(payload_pending)
payload_pending_force["force_new"] = True
r_pending_force = client.post("/api/v1/pix/send/intent", json=payload_pending_force, headers=headers)
results["pending_force_status"] = r_pending_force.status_code
results["pending_force_body"] = r_pending_force.json()
results["pending_force_send_key_unchanged"] = (
    r_pending_force.json().get("send_key") == k1_pending
)

# --- 6) equivalência de canonicalização quando descricao é vazia/None:
# reserve com descricao="" e send com descricao=None (ambos deveriam
# canonicalizar para "PIX" nos dois lugares, pelo MESMO "body.descricao or
# 'PIX'" já aplicado identicamente nas duas rotas) -> ack deve suceder. ---
payload_blank = {
    "chave_pix": "dest-blank@aurea.gold",
    "valor": 7.00,
    "descricao": "",
    "force_new": False,
}
r_blank_reserve = client.post("/api/v1/pix/send/intent", json=payload_blank, headers=headers)
k1_blank = r_blank_reserve.json().get("send_key")

send_blank_body = {"chave_pix": payload_blank["chave_pix"], "valor": payload_blank["valor"], "descricao": None}
r_blank_send = client.post(
    "/api/v1/pix/send",
    json=send_blank_body,
    headers={**headers, "Idempotency-Key": k1_blank},
)
r_blank_ack = client.post("/api/v1/pix/send/intent/ack", json={"send_key": k1_blank}, headers=headers)
results["blank_descricao_reserve_status"] = r_blank_reserve.status_code
results["blank_descricao_send_status"] = r_blank_send.status_code
results["blank_descricao_ack_status"] = r_blank_ack.status_code
results["blank_descricao_ack_body"] = r_blank_ack.json()

# --- isolamento entre usuários: outro usuário autenticado, mesmo payload,
# deve receber uma send_key DIFERENTE ---
other_user_id = make_user("intent-contract-other@test.local")
other_headers = login(client, "intent-contract-other@test.local")
r_other = client.post("/api/v1/pix/send/intent", json=payload_a, headers=other_headers)
results["other_user_send_key_isolated"] = (
    r_other.json().get("send_key") != k1 and r_other.json().get("send_key") != r_e.json().get("send_key")
)

# --- sem token -> 401/403 ---
r_noauth = client.post("/api/v1/pix/send/intent", json=payload_a)
results["noauth_status"] = r_noauth.status_code

print(json.dumps(results))
"""


def _run_probe() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "pix-intent-contract-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        # Banco descartável isolado, nunca backend/app.db.
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"

        proc = subprocess.run(
            [sys.executable, "-c", _PROBE_SCRIPT],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert proc.returncode == 0, (
            f"subprocess falhou:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )

        return json.loads(proc.stdout.strip().splitlines()[-1])


def test_pix_send_intent_http_contract():
    r = _run_probe()

    # A) reserva inicial
    assert r["a_status"] == 200, r["a_body"]
    assert r["a_body"]["state"] == "pending"
    assert r["a_body"]["send_key"]
    assert r["a_body"]["generation"] == 1
    assert r["a_body"]["can_send"] is True
    assert r["a_body"]["requires_explicit_new"] is False
    # 4) auth/isolation: user_id/ownerId injetados no body NUNCA são honrados
    assert r["a_intent_owner_matches_authenticated_user"] is True

    # B) envio
    assert r["b_status"] in (200, 201), r["b_body"]

    # C) ack — payload idêntico entre reserve e send -> deve suceder
    assert r["c_status"] == 200, r["c_body"]
    assert r["c_body"]["state"] == "acknowledged"

    # D) mesma operação depois do ack -> NÃO cria K2
    assert r["d_status"] == 200, r["d_body"]
    assert r["d_body"]["state"] == "acknowledged"
    assert r["d_body"]["can_send"] is False
    assert r["d_body"]["requires_explicit_new"] is True

    # E) força nova geração
    assert r["e_status"] == 200, r["e_body"]
    assert r["e_body"]["state"] == "pending"
    assert r["e_body"]["can_send"] is True
    assert r["e_body"]["generation"] == 2
    assert r["e_body"]["send_key"] != r["a_body"]["send_key"]

    # 3) pending + force_new=true -> 409 fail-closed, sem substituir K1
    assert r["pending_force_status"] == 409, r["pending_force_body"]
    assert r["pending_force_body"].get("force_new_rejected") is True
    assert r["pending_force_send_key_unchanged"] is True

    # 6) descricao "" (reserve) vs None (send) -> mesma canonicalização
    # ("body.descricao or 'PIX'" em ambas as rotas) -> ack sucede
    assert r["blank_descricao_reserve_status"] == 200
    assert r["blank_descricao_send_status"] in (200, 201)
    assert r["blank_descricao_ack_status"] == 200, r["blank_descricao_ack_body"]
    assert r["blank_descricao_ack_body"]["state"] == "acknowledged"

    # isolamento entre usuários
    assert r["other_user_send_key_isolated"] is True

    # sem token
    assert r["noauth_status"] in (401, 403)
