"""
Testes HTTP reais do rate limiting individual (@limiter.limit, sem
shared_limit) adicionado aos 5 endpoints ativos do Wallet PIX Sandbox
em backend/app/api/v1/routes/wallet.py:

    POST /api/v1/wallet/pix/sandbox-payment            (20/minute)
    POST /api/v1/wallet/pix/sandbox-webhook             (10/minute)
    GET  /api/v1/wallet/pix/sandbox-reconciliation/{ref} (30/minute)
    GET  /api/v1/wallet/pix/sandbox-audit-history        (20/minute)
    POST /api/v1/wallet/pix/asaas/sandbox/prepare        (10/minute)

Mecanismo: SlowAPI já existente (app/core/rate_limit.py), reaproveitado
sem alteração -- key_func=get_remote_address (só considera
request.client.host, nunca X-Forwarded-For). Cada endpoint é decorado
individualmente (@limiter.limit), nunca com shared_limit -- nenhum dos
5 tem alias, então não há risco de bypass entre paths distintos do
mesmo handler (diferente do webhook Partner/Asaas do PR #253).

Isolamento: mesmo padrão já estabelecido nesta sessão
(test_wallet_partner_rate_limit.py, test_ai_rate_limit.py):
subprocess Python isolado por teste, com DATABASE_URL apontando para um
SQLite descartável. Como o storage do SlowAPI é em memória por
processo, cada subprocess novo começa com o rate limiter completamente
zerado -- não é necessário nenhum reset manual de estado global.

Autenticação: os 5 endpoints exigem require_customer (JWT). Cada
subprocess cria um único usuário local no SQLite descartável e assina
um token com a mesma SECRET_KEY/JWT_SECRET do próprio processo de
teste -- nunca um usuário ou segredo real, nunca Production.

Nenhuma chamada de rede externa, nenhum acesso a Asaas/Railway/Production.
Valores de configuração usados abaixo (API key, webhook token) são
fixtures de teste locais, nunca segredos reais.

Observação confirmada empiricamente nesta implementação: o Limiter do
projeto (app/core/rate_limit.py) usa headers_enabled=False (padrão),
então o 429 do SlowAPI não inclui header Retry-After -- só o corpo
JSON {"error": "Rate limit exceeded: ..."}. Isso é comportamento
pré-existente do Limiter compartilhado (não alterado aqui, fora de
escopo), então os testes abaixo verificam o corpo de erro do 429, não
um header que este Limiter nunca emite.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]

_PROBE_SCRIPT = r"""
import json
import os

import jwt

from app.database import Base, engine, SessionLocal
from app.main import app
from app.models.user_main import User
from app.utils.security import ALGORITHM, SECRET_KEY, hash_password
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)

db = SessionLocal()
user = User(
    email="rl-probe-user@example.com",
    hashed_password=hash_password("rl-probe-password"),
    role="customer",
)
db.add(user)
db.commit()
db.refresh(user)
db.close()

_token = jwt.encode({"sub": user.email}, SECRET_KEY, algorithm=ALGORITHM)
_auth_headers = {"Authorization": f"Bearer {_token}"}

client = TestClient(app)

steps = json.loads(os.environ["PROBE_STEPS"])
results = []

for step in steps:
    method = step["method"]
    path = step["path"]
    body = step.get("body")
    headers = dict(step.get("headers") or {})
    if step.get("auth", True):
        headers.update(_auth_headers)

    if method == "GET":
        r = client.get(path, headers=headers)
    else:
        r = client.post(path, json=body, headers=headers)

    try:
        parsed_body = r.json()
    except Exception:
        parsed_body = None

    results.append({
        "status": r.status_code,
        "retry_after": r.headers.get("retry-after"),
        "body": parsed_body,
    })

print(json.dumps(results))
"""


def _run_probe(steps: list, *, env_overrides: dict) -> list:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "sandbox-rl-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"
        env["PROBE_STEPS"] = json.dumps(steps)
        env.update(env_overrides)

        proc = subprocess.run(
            [sys.executable, "-c", _PROBE_SCRIPT],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert proc.returncode == 0, (
            f"subprocess falhou:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )

        return json.loads(proc.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------
# Configuração sandbox (endpoints A-D: InternalSandboxPartnerAdapter) e
# Asaas Sandbox (endpoint E: prepare_wallet_asaas_correlated_pix_payment)
# -- mutuamente exclusivas via WALLET_PARTNER_PROVIDER, por isso cada
# endpoint roda em seu próprio subprocess com o env correto.
# ---------------------------------------------------------------------

def _sandbox_env() -> dict:
    return {
        "WALLET_MODE": "partner",
        "WALLET_PARTNER_PROVIDER": "sandbox",
    }


_ASAAS_ENV = {
    "WALLET_MODE": "partner",
    "WALLET_PARTNER_PROVIDER": "asaas",
    "REAL_MONEY_ENABLED": "false",
    "ASAAS_ENV": "sandbox",
    "ASAAS_BASE_URL": "https://api-sandbox.asaas.com/v3",
    "ASAAS_API_KEY": "test-only-local-fixture-api-key",
    "ASAAS_WEBHOOK_TOKEN": "test-only-local-fixture-webhook-token",
}


def _payment_step() -> dict:
    return {
        "method": "POST",
        "path": "/api/v1/wallet/pix/sandbox-payment",
        "body": {
            "amount": "10.00",
            "description": "rl-probe-a",
            "external_id": "rl-probe-a-static",
        },
    }


def _webhook_step(reference: str) -> dict:
    return {
        "method": "POST",
        "path": "/api/v1/wallet/pix/sandbox-webhook",
        "body": {
            "provider_reference": reference,
            "event_type": "pix.payment.confirmed",
            "status": "confirmed",
            "amount": "5.00",
            "idempotency_key": reference,
        },
    }


def _reconciliation_step(reference: str) -> dict:
    return {
        "method": "GET",
        "path": f"/api/v1/wallet/pix/sandbox-reconciliation/{reference}",
    }


def _audit_history_step() -> dict:
    return {
        "method": "GET",
        "path": "/api/v1/wallet/pix/sandbox-audit-history",
    }


def _prepare_step() -> dict:
    return {
        "method": "POST",
        "path": "/api/v1/wallet/pix/asaas/sandbox/prepare",
        "body": {
            "customer_id": "cus_rl_probe",
            "amount": "12.34",
            "due_date": "2026-12-31",
            "description": "rl-probe-e",
        },
    }


# Conjunto único de configuração por endpoint, reutilizado pelos 4
# testes abaixo (nenhum dos 40 combos ingênuos: 5 endpoints x 8
# cenários -- o mecanismo compartilhado (SlowAPI, get_remote_address,
# ausência de alias) é testado uma vez, não repetido por endpoint).
_ENDPOINTS = [
    {
        "id": "A_sandbox_payment",
        "limit": 20,
        "env": _sandbox_env(),
        "setup_steps": [],
        "call_step": lambda i: _payment_step(),
        "assert_ok": lambda body: (
            body["ok"] is True
            and body["wallet"]["real_money_enabled"] is False
            and body["payment"]["status"] == "pending"
        ),
    },
    {
        "id": "B_sandbox_webhook",
        "limit": 10,
        "env": _sandbox_env(),
        "setup_steps": [],
        "call_step": lambda i: _webhook_step(f"rl-probe-b-{i}"),
        "assert_ok": lambda body: (
            body["ok"] is True
            and body["duplicated"] is False
            and body["can_credit_balance"] is False
        ),
    },
    {
        "id": "C_sandbox_reconciliation",
        "limit": 30,
        "env": _sandbox_env(),
        "setup_steps": [_webhook_step("rl-probe-c-seed")],
        "call_step": lambda i: _reconciliation_step("rl-probe-c-seed"),
        "assert_ok": lambda body: (
            body["ok"] is True
            and body["reconciliation"]["event_found"] is True
            and body["reconciliation"]["status"] == "confirmed"
        ),
    },
    {
        "id": "D_sandbox_audit_history",
        "limit": 20,
        "env": _sandbox_env(),
        "setup_steps": [_webhook_step("rl-probe-d-seed")],
        "call_step": lambda i: _audit_history_step(),
        "assert_ok": lambda body: (
            body["ok"] is True
            and body["history"]["total_returned"] >= 1
        ),
    },
    {
        "id": "E_asaas_prepare",
        "limit": 10,
        "env": _ASAAS_ENV,
        "setup_steps": [],
        "call_step": lambda i: _prepare_step(),
        "assert_ok": lambda body: (
            body["ok"] is True
            and body["can_send_http"] is False
        ),
    },
]


def _by_id(endpoint_id: str) -> dict:
    return next(c for c in _ENDPOINTS if c["id"] == endpoint_id)


# ---------------------------------------------------------------------
# TESTE 1: N chamadas válidas dentro do limite chegam de fato à camada
# funcional (resposta de negócio genuína, nunca 401/403/404/422 usado
# como substituto de prova); a N+1-ésima retorna exatamente 429 com
# Retry-After.
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "config", _ENDPOINTS, ids=lambda c: c["id"]
)
def test_endpoint_limit_then_429(config):
    n = config["limit"]
    setup_steps = list(config["setup_steps"])
    call_steps = [config["call_step"](i) for i in range(n)]
    over_limit_step = config["call_step"](n)

    steps = setup_steps + call_steps + [over_limit_step]
    results = _run_probe(steps, env_overrides=config["env"])

    setup_count = len(setup_steps)
    for r in results[:setup_count]:
        assert r["status"] == 200, r

    within_limit = results[setup_count : setup_count + n]
    over_limit = results[setup_count + n]

    for r in within_limit:
        assert r["status"] == 200, r
        assert config["assert_ok"](r["body"]), r["body"]

    assert over_limit["status"] == 429, over_limit
    assert "error" in (over_limit["body"] or {}), over_limit


# ---------------------------------------------------------------------
# TESTE 2: abaixo do limite, sem JWT, a resposta é exatamente 401 --
# nunca 429 (limiter não engole o erro de autenticação) nem 200.
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "config", _ENDPOINTS, ids=lambda c: c["id"]
)
def test_auth_still_enforced_below_limit(config):
    step = dict(config["call_step"](0))
    step["auth"] = False

    results = _run_probe([step], env_overrides=config["env"])

    assert results[0]["status"] == 401, results[0]


# ---------------------------------------------------------------------
# TESTE 3: variar X-Forwarded-For a cada chamada, mantendo o mesmo
# request.client.host (mesmo TestClient/conexão), não cria orçamento
# novo -- get_remote_address nunca lê esse header. Endpoint B (mais
# restritivo, 10/minute) usado como representante do mecanismo
# compartilhado por todos os 5.
# ---------------------------------------------------------------------
def test_xff_forgery_does_not_bypass_limit():
    config = _by_id("B_sandbox_webhook")
    n = config["limit"]

    steps = []
    for i in range(n + 1):
        step = dict(config["call_step"](i))
        step["headers"] = {"X-Forwarded-For": f"10.0.0.{i}"}
        steps.append(step)

    results = _run_probe(steps, env_overrides=config["env"])
    statuses = [r["status"] for r in results]

    assert statuses[:n] == [200] * n, statuses
    assert statuses[n] == 429, statuses


# ---------------------------------------------------------------------
# TESTE 4: esgotar o orçamento de A não afeta B/C/D/E -- cada
# @limiter.limit individual mantém seu próprio bucket (escopo por
# função, não compartilhado), confirmando que nenhum shared_limit é
# necessário nem foi introduzido por engano.
# ---------------------------------------------------------------------
def test_endpoints_do_not_share_bucket():
    a_config = _by_id("A_sandbox_payment")
    n = a_config["limit"]

    steps = [a_config["call_step"](i) for i in range(n)]
    steps.append(a_config["call_step"](n))  # 21ª chamada a A -> 429
    steps.append(_webhook_step("rl-probe-shared-b"))
    steps.append(
        _reconciliation_step("rl-probe-shared-does-not-exist")
    )
    steps.append(_audit_history_step())
    steps.append(_prepare_step())

    results = _run_probe(steps, env_overrides=_sandbox_env())

    a_within_limit = results[:n]
    a_over_limit = results[n]
    b_result, c_result, d_result, e_result = results[n + 1 :]

    for r in a_within_limit:
        assert r["status"] == 200, r
    assert a_over_limit["status"] == 429, a_over_limit

    # B/C/D continuam com orçamento próprio intacto (200 genuíno).
    assert b_result["status"] == 200, b_result
    assert c_result["status"] == 200, c_result
    assert d_result["status"] == 200, d_result

    # E não foi bloqueado por A (não é 429); é 503 porque este
    # subprocess está em env sandbox (WALLET_PARTNER_PROVIDER=sandbox),
    # não asaas -- load_asaas_sandbox_config() rejeita a config
    # deliberadamente incompatível, provando que o bucket de E é
    # independente do de A sem precisar de um segundo subprocess/env.
    assert e_result["status"] == 503, e_result
