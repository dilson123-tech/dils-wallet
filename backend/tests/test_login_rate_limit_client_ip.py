"""
Testes da correção de segurança em rl_client_ip() (app/utils/rate_limit.py):
o rate limit de login deixou de confiar em X-Forwarded-For fornecido pela
própria requisição e passou a usar exclusivamente request.client.host.

Parte 1 (unitária, sem app/rede): exercita rl_client_ip() diretamente com
objetos de requisição mínimos (SimpleNamespace), provando os 4 cenários
pedidos (A, B, C, D).

Parte 2 (regressão de comportamento real via TestClient, subprocess
isolado -- mesmo padrão de test_pix_send_intent_http_contract.py e
test_main_startup_with_sentry.py, nunca toca backend/app.db): prova que
um atacante não consegue mais contornar o bucket por-IP do login apenas
variando X-Forwarded-For a cada tentativa.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from app.utils.rate_limit import rl_client_ip

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _fake_request(*, xff=None, client_host="203.0.113.10"):
    headers = {}
    if xff is not None:
        headers["x-forwarded-for"] = xff

    client = SimpleNamespace(host=client_host) if client_host is not None else None
    return SimpleNamespace(headers=headers, client=client)


# A) sem X-Forwarded-For: usa request.client.host
def test_uses_client_host_when_no_xff():
    req = _fake_request(xff=None, client_host="203.0.113.10")
    assert rl_client_ip(req) == "203.0.113.10"


# B) com X-Forwarded-For forjado: o header é ignorado, client.host prevalece
def test_ignores_forged_xff_and_keeps_client_host():
    req = _fake_request(xff="1.2.3.4", client_host="203.0.113.10")
    assert rl_client_ip(req) == "203.0.113.10"


# C) valores diferentes de X-Forwarded-For não mudam a identidade usada
def test_varying_xff_never_changes_resolved_identity():
    identities = {
        rl_client_ip(_fake_request(xff=xff, client_host="203.0.113.10"))
        for xff in ["1.1.1.1", "8.8.8.8", "9.9.9.9, 1.1.1.1", "not-an-ip", ""]
    }
    assert identities == {"203.0.113.10"}


# D) ausência segura de client/client.host -> fallback "unknown"
def test_missing_client_falls_back_to_unknown():
    assert rl_client_ip(_fake_request(xff="1.2.3.4", client_host=None)) == "unknown"

    req_no_host = SimpleNamespace(headers={"x-forwarded-for": "1.2.3.4"}, client=SimpleNamespace(host=None))
    assert rl_client_ip(req_no_host) == "unknown"


_PROBE_SCRIPT = r"""
import json

from app.database import Base, engine, SessionLocal
from app.utils.security import hash_password
from app.models.user_main import User
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)

db = SessionLocal()
db.add(User(email="victim@test.local", hashed_password=hash_password("correct-password"), role="customer"))
db.commit()
db.close()

client = TestClient(app)

statuses = []
for i in range(6):
    # Cada tentativa varia o X-Forwarded-For (o exato ataque que a correção
    # bloqueia) e usa um username diferente (para nunca esbarrar no bucket
    # por-identificador, isolando o teste no bucket por-IP).
    r = client.post(
        "/api/v1/auth/login",
        json={"username": f"attacker-{i}@test.local", "password": "wrong-password"},
        headers={"X-Forwarded-For": f"10.0.0.{i}"},
    )
    statuses.append(r.status_code)

print(json.dumps(statuses))
"""


def _run_login_bruteforce_probe() -> list:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "login-rl-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"

        # Limite baixo e determinístico só para este probe: isola o bucket
        # por-IP (3 tentativas) do bucket por-identificador (bem alto, para
        # nunca disparar primeiro e confundir o resultado).
        env["LOGIN_RL_ENABLED"] = "1"
        env["LOGIN_RL_WINDOW_SEC"] = "60"
        env["LOGIN_RL_MAX_PER_IP"] = "3"
        env["LOGIN_RL_MAX_PER_IDENT"] = "1000"

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

        return __import__("json").loads(proc.stdout.strip().splitlines()[-1])


def test_login_cannot_bypass_per_ip_bucket_by_varying_xff():
    statuses = _run_login_bruteforce_probe()

    # As 3 primeiras tentativas consomem o bucket por-IP (max=3); a partir
    # da 4ª, mesmo com um X-Forwarded-For e um username novos a cada vez,
    # o bucket por-IP (chaveado por request.client.host, constante para
    # todas as chamadas deste TestClient) já deve estar esgotado.
    assert statuses[:3] == [401, 401, 401], statuses
    assert 429 in statuses[3:], statuses
