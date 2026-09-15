"""
Testes HTTP reais do rate limiting adicionado ao receptor de webhook
Partner/Asaas (handle_asaas_sandbox_webhook_receiver, em
backend/app/api/v1/routes/wallet.py), que atende aos três aliases:

    POST /api/v1/partners
    POST /api/v1/partners/
    POST /api/v1/partners/asaas/webhooks/sandbox

Mecanismo: @limiter.shared_limit("30/minute", scope="partner_asaas_webhook")
-- SlowAPI já existente (app/core/rate_limit.py), reaproveitado sem
alteração. O `scope` fixo garante que os três aliases consomem o MESMO
bucket por IP, apesar de o Limiter deste projeto usar key_style="url"
(que, sem esse scope explícito, escoparia cada alias separadamente).

Isolamento: mesmo padrão já estabelecido nesta sessão
(test_ai_rate_limit.py, test_refresh_rate_limit.py, test_login_rate_limit_client_ip.py):
subprocess Python isolado por teste, com DATABASE_URL apontando para um
SQLite descartável. Como o storage do SlowAPI (assim como o `_BUCKETS`
artesanal) é em memória, por processo, cada subprocess novo começa com
o rate limiter completamente zerado -- não é necessário nenhum reset
manual de estado global, e nenhum teste deste arquivo pode vazar estado
para outro (nem para os testes de test_asaas_webhook_receiver.py, que
isolam seu próprio orçamento por IP dedicado por teste, sem tocar este
mecanismo via HTTP).

Nenhuma chamada de rede externa, nenhum acesso a Asaas/Railway/Production.
Valores de configuração usados abaixo (API key, webhook token) são
fixtures de teste locais, nunca segredos reais.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

_PARTNER_PATHS = [
    "/api/v1/partners",
    "/api/v1/partners/",
    "/api/v1/partners/asaas/webhooks/sandbox",
]

_PROBE_SCRIPT = r"""
import json
import os

from app.database import Base, engine
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)

client = TestClient(app)

steps = json.loads(os.environ["PROBE_STEPS"])
results = []

for step in steps:
    headers = dict(step.get("headers") or {})
    r = client.post(step["path"], json=step.get("body", {}), headers=headers)
    results.append({"status": r.status_code, "retry_after": r.headers.get("retry-after")})

print(json.dumps(results))
"""

# Config Asaas Sandbox válida (fixture de teste local, não é segredo real)
# -- necessária para o handler alcançar a checagem de token em vez de
# retornar 503 por config ausente/inválida.
_VALID_ASAAS_ENV = {
    "WALLET_MODE": "partner",
    "WALLET_PARTNER_PROVIDER": "asaas",
    "REAL_MONEY_ENABLED": "false",
    "ASAAS_ENV": "sandbox",
    "ASAAS_BASE_URL": "https://api-sandbox.asaas.com/v3",
    "ASAAS_API_KEY": "test-only-local-fixture-api-key",
    "ASAAS_WEBHOOK_TOKEN": "test-only-local-fixture-webhook-token",
}


def _run_probe(steps: list, *, env_overrides: dict | None = None) -> list:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "partner-rl-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"
        env["PROBE_STEPS"] = json.dumps(steps)
        if env_overrides:
            env.update(env_overrides)

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


# 1) BASIC LIMIT: orçamento de 30/minute por IP; a 31ª chamada estoura.
# Sem header asaas-access-token -> cada chamada dentro do limite retorna
# 401 (funcional, não 429) -- prova que abaixo do limite o comportamento
# normal é preservado.
def test_basic_limit_30_per_minute_then_429():
    steps = [
        {"path": "/api/v1/partners", "body": {}}
        for _ in range(35)
    ]
    results = _run_probe(steps, env_overrides=_VALID_ASAAS_ENV)
    statuses = [r["status"] for r in results]

    assert statuses[:30] == [401] * 30, statuses
    assert 429 in statuses[30:], statuses


# 2) SHARED ALIASES: alternar entre os três paths NÃO multiplica o
# orçamento -- as 30 primeiras chamadas (somadas entre os três aliases)
# passam, e a partir da 31ª qualquer um dos três aliases já retorna 429.
# Se o orçamento não fosse compartilhado, seria possível emplacar até
# ~90 chamadas (30 por alias) antes do primeiro 429.
def test_shared_budget_across_three_path_aliases():
    steps = [
        {"path": _PARTNER_PATHS[i % 3], "body": {}}
        for i in range(35)
    ]
    results = _run_probe(steps, env_overrides=_VALID_ASAAS_ENV)
    statuses = [r["status"] for r in results]

    assert statuses[:30] == [401] * 30, statuses
    assert 429 in statuses[30:], statuses

    # confirma explicitamente que NENHUMA das 35 tentativas passou de
    # 30 respostas funcionais (401) -- ou seja, não houve 90 requests
    # bem-sucedidas por alternância de alias.
    assert statuses.count(401) == 30, statuses


# 3) FORGED X-FORWARDED-FOR: variar o header a cada chamada, mantendo o
# mesmo client host real do TestClient, não cria orçamentos novos --
# mesmo comportamento já corrigido em rl_client_ip (não confia em XFF).
# Este teste prova apenas o comportamento NESTE ambiente de teste
# (TestClient, sem proxy real na frente); não faz nenhuma afirmação
# sobre o comportamento real do proxy do Railway, que permanece
# INCONCLUSIVO e fora de escopo.
def test_forged_x_forwarded_for_does_not_bypass_limit():
    steps = [
        {
            "path": "/api/v1/partners",
            "body": {},
            "headers": {"X-Forwarded-For": f"10.0.0.{i}"},
        }
        for i in range(35)
    ]
    results = _run_probe(steps, env_overrides=_VALID_ASAAS_ENV)
    statuses = [r["status"] for r in results]

    assert statuses[:30] == [401] * 30, statuses
    assert 429 in statuses[30:], statuses


# 4) Comportamento funcional abaixo do limite, preservado:

def test_missing_token_header_returns_401():
    results = _run_probe(
        [{"path": "/api/v1/partners", "body": {}}],
        env_overrides=_VALID_ASAAS_ENV,
    )
    assert results[0]["status"] == 401, results


def test_invalid_token_returns_403():
    results = _run_probe(
        [{
            "path": "/api/v1/partners",
            "body": {},
            "headers": {"asaas-access-token": "wrong-token"},
        }],
        env_overrides=_VALID_ASAAS_ENV,
    )
    assert results[0]["status"] == 403, results


def test_invalid_config_fails_closed_with_503():
    # Config Asaas Sandbox deliberadamente incompleta (sem
    # WALLET_PARTNER_PROVIDER/ASAAS_ENV corretos) -- fixture local,
    # nenhum segredo real envolvido. load_asaas_sandbox_config() deve
    # levantar AsaasConfigError, e o handler responde 503 (fail-closed)
    # antes mesmo de checar o token.
    broken_env = {
        "WALLET_MODE": "demo",  # inválido de propósito: precisa ser "partner"
    }
    results = _run_probe(
        [{
            "path": "/api/v1/partners",
            "body": {},
            "headers": {"asaas-access-token": "test-only-local-fixture-webhook-token"},
        }],
        env_overrides=broken_env,
    )
    assert results[0]["status"] == 503, results
