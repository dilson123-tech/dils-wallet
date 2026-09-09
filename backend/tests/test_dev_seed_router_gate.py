"""
B1 — o router de desenvolvimento (dev_seed) só deve ser registrado
(`app.include_router(dev_seed.router)`) quando ALLOW_DEV_SEED indicar
habilitado explicitamente.

Cada cenário roda em um subprocess Python isolado, com a variável de
ambiente definida ANTES de importar app.main. Isso evita falso
positivo/negativo por cache de import: app.main é importado uma única
vez por processo (`sys.modules`), e pytest roda todos os testes do
arquivo no mesmo processo por padrão — reimportar dentro do mesmo
processo não re-executaria o registro condicional do router.

Nenhum banco real é usado: cada subprocess recebe um DATABASE_URL
próprio, apontando para um arquivo SQLite descartável num diretório
temporário (nunca backend/app.db).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]

_PROBE_SCRIPT = """
import json
from app.main import app

result = {"has_dev_seed_ping": "/dev-seed/ping" in app.openapi()["paths"]}

if __RUN_DEFENSE_PROBE__:
    from fastapi.testclient import TestClient
    client = TestClient(app)
    resp = client.post("/dev-seed/admin-reset-passwd")
    result["admin_reset_passwd_status"] = resp.status_code

print(json.dumps(result))
"""


def _run_probe(env_overrides: dict, run_defense_probe: bool = False) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "b1-gate-test-dummy-secret"
        # Banco descartável isolado, nunca backend/app.db.
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"

        # Nunca herdar essas variáveis do ambiente real por acidente —
        # cada cenário controla explicitamente o que precisa via
        # env_overrides.
        for key in ("ALLOW_DEV_SEED", "ADMIN_SEED_TOKEN", "AUREA_DEV_SECRET", "ADMIN_TEMP_PASSWORD"):
            env.pop(key, None)

        env.update(env_overrides)

        script = _PROBE_SCRIPT.replace("__RUN_DEFENSE_PROBE__", str(run_defense_probe))

        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert proc.returncode == 0, (
            f"subprocess falhou (env_overrides={env_overrides}):\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )

        return json.loads(proc.stdout.strip().splitlines()[-1])


# --- Caso A: default fail-closed (ALLOW_DEV_SEED ausente) ---
def test_default_without_allow_dev_seed_router_not_mounted():
    result = _run_probe({})
    assert result["has_dev_seed_ping"] is False


# --- Caso B: valores desabilitados ---
@pytest.mark.parametrize(
    "value",
    ["", "0", "false", "off", "no", "garbage"],
)
def test_disabled_values_router_not_mounted(value):
    result = _run_probe({"ALLOW_DEV_SEED": value})
    assert result["has_dev_seed_ping"] is False


# --- Caso C: todos os enables canônicos, incluindo case-insensitive ---
@pytest.mark.parametrize(
    "value",
    ["1", "true", "yes", "on", "TRUE"],
)
def test_enabled_values_router_mounted(value):
    result = _run_probe({"ALLOW_DEV_SEED": value})
    assert result["has_dev_seed_ping"] is True


# --- Caso D: defesa em profundidade — router montado, guard interno
# continua exigindo token mesmo sem nenhuma operação de banco real ---
def test_router_mounted_but_internal_guard_still_required():
    result = _run_probe({"ALLOW_DEV_SEED": "1"}, run_defense_probe=True)
    assert result["has_dev_seed_ping"] is True
    assert result["admin_reset_passwd_status"] == 404
