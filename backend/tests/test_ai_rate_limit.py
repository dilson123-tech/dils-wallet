"""
Testes do rate limiting por IP adicionado aos 8 endpoints ativos de
IA/chat (backend/app/api/v1/routes/ai_chat.py, ai.py, assist.py e
backend/app/api/v1/ai/chat_lab.py), usando o SlowAPI já existente
(backend/app/core/rate_limit.py) -- mesmo padrão já usado em
/api/v1/pix/send.

Nenhum teste aqui usa backend/app/utils/rate_limit.py (_BUCKETS): essa
correção não toca o limiter artesanal.

Todos os cenários que exercitam os endpoints reais usam o padrão já
estabelecido neste repositório: subprocess Python isolado, com
DATABASE_URL apontando para um SQLite descartável, nunca toca
backend/app.db. Isso também garante que cada cenário começa com o
estado do SlowAPI limpo (processo novo).

Nenhum teste faz chamada real a OpenAI ou qualquer outro provedor
externo: os 8 endpoints protegidos aqui não chamam nenhum provedor de
IA externo hoje (confirmado por investigação dedicada -- os únicos
caminhos que chamariam OpenAI são código morto, não montado no app).
O único acesso de rede que alguns desses endpoints fazem é uma chamada
HTTP interna ao próprio processo (http://127.0.0.1:8000); os testes
abaixo usam limites baixos o suficiente para bloquear (429) antes que
esse caminho interno seja alcançado, então essa chamada não chega a
ocorrer nos cenários de bloqueio -- e nos cenários "abaixo do limite"
ela pode falhar (connection refused, já que não há servidor real
escutando na porta 8000 durante o teste) sem quebrar a asserção, pois
os handlers tratam esse erro internamente e retornam 200 com um
fallback textual, não uma exceção.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

_ENDPOINTS = {
    "chat": ("POST", "/api/v1/ai/chat", {"message": "oi"}),
    "pagamentos_lab": ("POST", "/api/v1/ai/pagamentos_lab", {"message": "oi"}),
    "pix_insight": ("POST", "/api/v1/ai/ai/pix-insight", None),
    "headline": ("POST", "/api/v1/ai/headline", None),
    "headline_lab": ("POST", "/api/v1/ai/headline-lab", None),
    "summary": ("GET", "/api/v1/ai/summary", None),
    "assist": ("POST", "/api/v1/ai/assist", {"msg": "oi"}),
    "chat_lab": ("POST", "/api/v1/ai/chat_lab", {"message": "oi"}),
}

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
    method = step["method"]
    path = step["path"]
    body = step.get("body")
    headers = step.get("headers") or {}

    if method == "GET":
        r = client.get(path, headers=headers)
    else:
        r = client.post(path, json=body, headers=headers)

    results.append({
        "status": r.status_code,
        "retry_after": r.headers.get("retry-after"),
    })

print(json.dumps(results))
"""


def _run_probe(steps: list) -> list:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "ai-rl-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"
        env["PROBE_STEPS"] = json.dumps(steps)

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


def _step(name: str, **extra) -> dict:
    method, path, body = _ENDPOINTS[name]
    step = {"method": method, "path": path}
    if body is not None:
        step["body"] = body
    step.update(extra)
    return step


# A) os 8 endpoints estão efetivamente registrados com rate limiting:
# uma única chamada a cada um funciona normalmente (nenhum 429/500 por
# causa do wiring do decorator), e o limite de 31 chamadas no MESMO
# endpoint estoura em 429 -- provando que o decorator está de fato
# ativo em cada rota, uma de cada vez.
def test_all_8_endpoints_are_registered_with_rate_limiting():
    for name in _ENDPOINTS:
        steps = [_step(name) for _ in range(31)]
        results = _run_probe(steps)
        statuses = [r["status"] for r in results]
        assert 429 in statuses, (name, statuses)
        # a resposta 429 não deve ser a primeira (a primeira chamada
        # tem que funcionar normalmente -- prova que o rate limit não
        # quebrou o comportamento funcional preexistente).
        assert statuses[0] != 429, (name, statuses)


# B) chamadas repetidas do MESMO IP recebem 429 ao exceder o limite
# (30/minute) -- verificado em detalhe para o endpoint mais exposto.
def test_repeated_calls_same_ip_hit_429_after_limit():
    steps = [_step("chat") for _ in range(35)]
    results = _run_probe(steps)
    statuses = [r["status"] for r in results]

    assert statuses[:30].count(429) == 0, statuses
    assert 429 in statuses[30:], statuses


# C) variar X-Forwarded-For não permite bypass no ambiente de teste
# (request.client permanece o mesmo -- TestClient -- então o SlowAPI,
# via get_remote_address, sempre resolve o mesmo IP).
def test_varying_xff_does_not_bypass_limit():
    steps = [
        _step("chat", headers={"X-Forwarded-For": f"10.0.0.{i}"})
        for i in range(35)
    ]
    results = _run_probe(steps)
    statuses = [r["status"] for r in results]
    assert 429 in statuses, statuses


# D) variar X-User-Email/user_id não cria uma segunda dimensão nem
# permite contornar o limite -- todas as chamadas, com identidades
# diferentes, ainda caem no mesmo bucket por IP.
def test_varying_declared_identity_does_not_bypass_limit():
    steps = [
        _step("chat", headers={"X-User-Email": f"user-{i}@test.local"})
        for i in range(35)
    ]
    results = _run_probe(steps)
    statuses = [r["status"] for r in results]
    assert 429 in statuses, statuses

    # também para o corpo (assist aceita user_id no body)
    steps_body = [
        {"method": "POST", "path": "/api/v1/ai/assist", "body": {"msg": "oi", "user_id": i}}
        for i in range(35)
    ]
    results_body = _run_probe(steps_body)
    statuses_body = [r["status"] for r in results_body]
    assert 429 in statuses_body, statuses_body


# E) requests abaixo do limite mantêm o comportamento HTTP funcional
# preexistente (200, sem 429/500) para cada um dos 8 endpoints.
def test_requests_below_limit_keep_previous_functional_behavior():
    for name in _ENDPOINTS:
        results = _run_probe([_step(name)])
        assert results[0]["status"] == 200, (name, results)


# G) a implementação não usa backend/app/utils/rate_limit.py nem cria
# novas chaves em _BUCKETS -- confirmado inspecionando o estado do
# limiter artesanal após bater nos 8 endpoints repetidamente.
def test_no_new_buckets_created_in_artisanal_limiter():
    probe = r"""
import json
import os

from app.database import Base, engine
from app.main import app
from fastapi.testclient import TestClient
from app.utils.rate_limit import _BUCKETS

Base.metadata.create_all(bind=engine)

before = dict(_BUCKETS)

client = TestClient(app)
for _ in range(10):
    client.post("/api/v1/ai/chat", json={"message": "oi"})
    client.post("/api/v1/ai/assist", json={"msg": "oi", "user_id": 1})
    client.get("/api/v1/ai/summary")

after = dict(_BUCKETS)

print(json.dumps({
    "before_keys": sorted(before.keys()),
    "after_keys": sorted(after.keys()),
}))
"""
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "ai-rl-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"

        proc = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 0, (
            f"subprocess falhou:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
        out = json.loads(proc.stdout.strip().splitlines()[-1])

    assert out["before_keys"] == [], out
    assert out["after_keys"] == [], out
