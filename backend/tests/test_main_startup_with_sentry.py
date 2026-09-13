"""
Teste de startup: confirma que app.main importa e o app sobe normalmente
com o wiring de setup_sentry() em vigor, em dois cenários -- sem
SENTRY_DSN (caso comum de dev/CI) e com SENTRY_DSN sintaticamente válido.

Mesmo padrão de isolamento já usado em test_dev_seed_router_gate.py e
test_pix_send_intent_http_contract.py: subprocess isolado, DATABASE_URL
apontando para um SQLite descartável, nunca toca backend/app.db.

O DSN usado no segundo cenário aponta deliberadamente para loopback
(127.0.0.1), NÃO para um host real de sentry.io. Isso importa porque o
sentry-sdk tem `auto_session_tracking=True` por padrão, e a integração
ASGI/Starlette dispara `track_session(...)` a cada requisição -- ou seja,
o SDK real, mesmo sem nenhuma exceção capturada, tenta enviar um envelope
de sessão em background após o GET em /healthz. Com um host de internet
real isso seria uma tentativa de conexão de saída de verdade (confirmado
empiricamente com um probe de socket antes desta correção). Com
127.0.0.1:1 essa tentativa fica confinada à própria máquina e falha
instantaneamente (nada escuta nessa porta), sem jamais alcançar a
internet -- o SDK real continua sendo exercitado (init, integrations,
options), só o destino do transporte é que nunca sai do host local.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

_PROBE_SCRIPT = r"""
from app.database import Base, engine
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)

client = TestClient(app)
r = client.get("/healthz")
assert r.status_code == 200, (r.status_code, r.text)
print("OK")
"""


def _run_probe(*, sentry_dsn: str | None) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "sentry-startup-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"

        if sentry_dsn is None:
            env.pop("SENTRY_DSN", None)
        else:
            env["SENTRY_DSN"] = sentry_dsn

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
        assert proc.stdout.strip().splitlines()[-1] == "OK"


def test_app_boots_without_sentry_dsn():
    _run_probe(sentry_dsn=None)


def test_app_boots_with_syntactically_valid_sentry_dsn():
    # Loopback deliberado (ver docstring do módulo): DSN sintaticamente
    # válido o bastante para setup_sentry() inicializar o SDK real, mas
    # cujo destino de transporte nunca sai de 127.0.0.1 -- nenhuma porta
    # escuta em :1, então qualquer tentativa de envio falha localmente e
    # instantaneamente, sem alcançar a internet.
    _run_probe(sentry_dsn="https://public@127.0.0.1:1/1")
