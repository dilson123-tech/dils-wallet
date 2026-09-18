"""
Testes do rate limiting por IP adicionado aos 7 endpoints ativos de
IA/chat (backend/app/api/v1/routes/ai_chat.py, ai.py, assist.py),
usando o SlowAPI já existente (backend/app/core/rate_limit.py) --
mesmo padrão já usado em /api/v1/pix/send.

Bloco 3J: POST /api/v1/ai/chat_lab (backend/app/api/v1/ai/chat_lab.py)
foi removido -- endpoint órfão/quebrado, sem caller vivo no frontend e
sem caminho de dados funcional (a chamada interna para pix.py nunca
encaminhava Authorization, então qualquer intent além de "geral"
sempre respondia 500). Saiu de _ENDPOINTS abaixo.

Nenhum teste aqui usa backend/app/utils/rate_limit.py (_BUCKETS): essa
correção não toca o limiter artesanal.

Todos os cenários que exercitam os endpoints reais usam o padrão já
estabelecido neste repositório: subprocess Python isolado, com
DATABASE_URL apontando para um SQLite descartável, nunca toca
backend/app.db. Isso também garante que cada cenário começa com o
estado do SlowAPI limpo (processo novo).

Nenhum teste faz chamada real a OpenAI ou qualquer outro provedor
externo: os 7 endpoints protegidos aqui não chamam nenhum provedor de
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

Atualizado após a correção de segurança em
POST /api/v1/ai/ai/pix-insight (branch
security/ai-chat-pix-insight-auth, ver
tests/test_ai_chat_pix_insight_auth.py): esse endpoint passou a exigir
Depends(require_customer) -- identidade vem sempre do token Bearer
autenticado, nunca do header X-User-Email. Por isso ele não pode mais
compartilhar os cenários genéricos "sem token" dos outros endpoints
(_ENDPOINTS abaixo): sem token, ele agora responde 401 antes mesmo do
SlowAPI contar a chamada, então a cobertura de rate limit dele foi
movida para dois testes dedicados que sempre autenticam a chamada com
um usuário real, criado no próprio banco SQLite descartável do
subprocess e assinado com o mesmo SECRET_KEY/JWT_SECRET do ambiente de
teste (via app.utils.security.create_access_token, a mesma função
canônica usada em produção -- nenhuma lógica de JWT é reimplementada
aqui).

Atualizado de novo (issue #271) após os Blocos 3E e 3F: POST
/api/v1/ai/chat (Bloco 3E, security/ai-chat-auth-characterization-
block3e) e GET /api/v1/ai/summary (Bloco 3F,
security/ai-summary-auth-characterization-block3f) também passaram a
exigir Depends(require_customer). Pelo mesmo motivo do pix_insight,
os dois saíram de _ENDPOINTS e ganharam a mesma cobertura dedicada
(401 sem token + rate limit efetivo com token válido). Os cenários
"IP repetido" / "XFF variável" / "identidade declarada variável" que
antes exercitavam /api/v1/ai/chat sem token agora autenticam a
chamada primeiro (mesmo padrão de auth_user_email já usado para
pix_insight), preservando a mesma cobertura desses três eixos de
bypass contra o novo contrato autenticado.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Os 4 endpoints que continuam sem exigir autenticação -- cobertura
# genérica inalterada (testes A e E abaixo). pix_insight, chat e
# summary saíram deste dict porque hoje exigem Depends(require_customer):
# suas coberturas de rate limit vivem em testes dedicados
# (test_pix_insight_*, test_chat_*, test_summary_* abaixo). chat_lab
# saiu por ter sido removido no Bloco 3J (endpoint órfão/quebrado).
_ENDPOINTS = {
    "pagamentos_lab": ("POST", "/api/v1/ai/pagamentos_lab", {"message": "oi"}),
    "headline": ("POST", "/api/v1/ai/headline", None),
    "headline_lab": ("POST", "/api/v1/ai/headline-lab", None),
    "assist": ("POST", "/api/v1/ai/assist", {"msg": "oi"}),
}

_CHAT_STEP = ("POST", "/api/v1/ai/chat", {"message": "oi"})
_SUMMARY_STEP = ("GET", "/api/v1/ai/summary", None)

# _step() abaixo também sabe montar chamadas para chat/summary (usado
# pelos testes B/C/D, que agora autenticam a chamada antes de testar
# os eixos de bypass), mesmo eles não fazendo mais parte de _ENDPOINTS.
_ALL_STEPS = {**_ENDPOINTS, "chat": _CHAT_STEP, "summary": _SUMMARY_STEP}

_PIX_INSIGHT_PATH = "/api/v1/ai/ai/pix-insight"
_PIX_INSIGHT_AUTH_EMAIL = "ai-rate-limit-probe@test.local"
_CHAT_AUTH_EMAIL = "ai-rate-limit-chat-probe@test.local"
_SUMMARY_AUTH_EMAIL = "ai-rate-limit-summary-probe@test.local"

_PROBE_SCRIPT = r"""
import json
import os

from app.database import Base, engine, SessionLocal
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Se PROBE_AUTH_USER_EMAIL estiver definido, cria esse usuário no
# banco descartável deste subprocess e assina um token de acesso real
# para ele, via a mesma função canônica usada em produção -- nenhuma
# lógica de JWT é reimplementada aqui.
auth_token = None
auth_email = os.environ.get("PROBE_AUTH_USER_EMAIL")
if auth_email:
    from app.models.user_main import User
    from app.utils.security import create_access_token, hash_password

    db = SessionLocal()
    try:
        db.add(User(email=auth_email, hashed_password=hash_password("x"), role="customer"))
        db.commit()
    finally:
        db.close()
    auth_token = create_access_token({"sub": auth_email})

steps = json.loads(os.environ["PROBE_STEPS"])
results = []

for step in steps:
    method = step["method"]
    path = step["path"]
    body = step.get("body")
    headers = dict(step.get("headers") or {})
    if step.get("auth"):
        headers["Authorization"] = f"Bearer {auth_token}"

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


def _run_probe(steps: list, *, auth_user_email: str | None = None) -> list:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "ai-rl-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"
        env["PROBE_STEPS"] = json.dumps(steps)
        if auth_user_email:
            env["PROBE_AUTH_USER_EMAIL"] = auth_user_email

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
    method, path, body = _ALL_STEPS[name]
    step = {"method": method, "path": path}
    if body is not None:
        step["body"] = body
    step.update(extra)
    return step


# A) os 4 endpoints sem autenticação estão efetivamente registrados
# com rate limiting: uma única chamada a cada um funciona normalmente
# (nenhum 429/500 por causa do wiring do decorator), e o limite de 31
# chamadas no MESMO endpoint estoura em 429 -- provando que o
# decorator está de fato ativo em cada rota, uma de cada vez.
# pix_insight, chat e summary (os outros 3 endpoints ativos) têm
# cobertura equivalente, mas autenticada, nos testes dedicados abaixo
# (test_pix_insight_*, test_chat_*, test_summary_*).
def test_all_4_unauthenticated_endpoints_are_registered_with_rate_limiting():
    for name in _ENDPOINTS:
        steps = [_step(name) for _ in range(31)]
        results = _run_probe(steps)
        statuses = [r["status"] for r in results]
        assert 429 in statuses, (name, statuses)
        # a resposta 429 não deve ser a primeira (a primeira chamada
        # tem que funcionar normalmente -- prova que o rate limit não
        # quebrou o comportamento funcional preexistente).
        assert statuses[0] != 429, (name, statuses)


# A2) pix_insight, sem token, responde 401 -- nunca 200/500 -- em toda
# a faixa testada (1 chamada é suficiente para provar o contrato; não
# há necessidade de estourar o limite aqui, isso é feito com token
# válido no teste seguinte).
def test_pix_insight_requires_valid_authentication_now():
    results = _run_probe([{"method": "POST", "path": _PIX_INSIGHT_PATH}])
    assert results[0]["status"] == 401, results


# A3) pix_insight, autenticado com um token válido (usuário real criado
# no banco descartável do subprocess, token assinado pela função
# canônica create_access_token), continua coberto pelo mesmo rate
# limit "30/minute": a primeira chamada funciona (200), e a 31ª estoura
# em 429 -- mesma prova da A, agora sob o novo contrato autenticado.
def test_pix_insight_rate_limit_enforced_with_valid_authentication():
    steps = [
        {"method": "POST", "path": _PIX_INSIGHT_PATH, "auth": True}
        for _ in range(31)
    ]
    results = _run_probe(steps, auth_user_email=_PIX_INSIGHT_AUTH_EMAIL)
    statuses = [r["status"] for r in results]
    assert statuses[0] == 200, statuses
    assert statuses[:30].count(429) == 0, statuses
    assert 429 in statuses[30:], statuses


# A4) chat (POST /api/v1/ai/chat), sem token, responde 401 -- nunca
# 200/500 -- desde a canonicalização de auth do Bloco 3E. Mesmo padrão
# do A2 para pix_insight.
def test_chat_requires_valid_authentication_now():
    results = _run_probe([{"method": "POST", "path": _CHAT_STEP[1], "body": _CHAT_STEP[2]}])
    assert results[0]["status"] == 401, results


# A5) chat, autenticado com um token válido, continua coberto pelo
# mesmo rate limit "30/minute": 1ª chamada funciona (200), 31ª estoura
# em 429. Mesmo padrão do A3 para pix_insight.
def test_chat_rate_limit_enforced_with_valid_authentication():
    steps = [
        {"method": "POST", "path": _CHAT_STEP[1], "body": _CHAT_STEP[2], "auth": True}
        for _ in range(31)
    ]
    results = _run_probe(steps, auth_user_email=_CHAT_AUTH_EMAIL)
    statuses = [r["status"] for r in results]
    assert statuses[0] == 200, statuses
    assert statuses[:30].count(429) == 0, statuses
    assert 429 in statuses[30:], statuses


# A6) summary (GET /api/v1/ai/summary), sem token, responde 401 --
# nunca 200/500 -- desde a canonicalização de auth do Bloco 3F. Mesmo
# padrão do A2 para pix_insight.
def test_summary_requires_valid_authentication_now():
    results = _run_probe([{"method": "GET", "path": _SUMMARY_STEP[1]}])
    assert results[0]["status"] == 401, results


# A7) summary, autenticado com um token válido, continua coberto pelo
# mesmo rate limit "30/minute": 1ª chamada funciona (200), 31ª estoura
# em 429. Mesmo padrão do A3 para pix_insight.
def test_summary_rate_limit_enforced_with_valid_authentication():
    steps = [
        {"method": "GET", "path": _SUMMARY_STEP[1], "auth": True}
        for _ in range(31)
    ]
    results = _run_probe(steps, auth_user_email=_SUMMARY_AUTH_EMAIL)
    statuses = [r["status"] for r in results]
    assert statuses[0] == 200, statuses
    assert statuses[:30].count(429) == 0, statuses
    assert 429 in statuses[30:], statuses


# B) chamadas repetidas do MESMO IP recebem 429 ao exceder o limite
# (30/minute) -- verificado em detalhe para o endpoint mais exposto
# (chat), agora autenticando a chamada primeiro (chat exige
# Depends(require_customer) desde o Bloco 3E; sem token, o SlowAPI
# nunca chega a contar a chamada -- ver test_chat_requires_valid_authentication_now).
def test_repeated_calls_same_ip_hit_429_after_limit():
    steps = [_step("chat", auth=True) for _ in range(35)]
    results = _run_probe(steps, auth_user_email=_CHAT_AUTH_EMAIL)
    statuses = [r["status"] for r in results]

    assert statuses[:30].count(429) == 0, statuses
    assert 429 in statuses[30:], statuses


# C) variar X-Forwarded-For não permite bypass no ambiente de teste
# (request.client permanece o mesmo -- TestClient -- então o SlowAPI,
# via get_remote_address, sempre resolve o mesmo IP). Chamada
# autenticada, pelo mesmo motivo do teste B.
def test_varying_xff_does_not_bypass_limit():
    steps = [
        _step("chat", auth=True, headers={"X-Forwarded-For": f"10.0.0.{i}"})
        for i in range(35)
    ]
    results = _run_probe(steps, auth_user_email=_CHAT_AUTH_EMAIL)
    statuses = [r["status"] for r in results]
    assert 429 in statuses, statuses


# D) variar X-User-Email/user_id não cria uma segunda dimensão nem
# permite contornar o limite -- todas as chamadas, com identidades
# declaradas diferentes, ainda caem no mesmo bucket por IP (a
# identidade real, do token, é sempre a mesma -- X-User-Email nunca
# selecionou identidade, mesmo antes do Bloco 3E). Chamada autenticada,
# pelo mesmo motivo do teste B.
def test_varying_declared_identity_does_not_bypass_limit():
    steps = [
        _step("chat", auth=True, headers={"X-User-Email": f"user-{i}@test.local"})
        for i in range(35)
    ]
    results = _run_probe(steps, auth_user_email=_CHAT_AUTH_EMAIL)
    statuses = [r["status"] for r in results]
    assert 429 in statuses, statuses

    # também para o corpo (assist aceita user_id no body; assist
    # continua genuinamente sem autenticação, não precisa de token)
    steps_body = [
        {"method": "POST", "path": "/api/v1/ai/assist", "body": {"msg": "oi", "user_id": i}}
        for i in range(35)
    ]
    results_body = _run_probe(steps_body)
    statuses_body = [r["status"] for r in results_body]
    assert 429 in statuses_body, statuses_body


# E) requests abaixo do limite mantêm o comportamento HTTP funcional
# preexistente (200, sem 429/500) para cada um dos 4 endpoints sem
# autenticação. pix_insight, chat e summary têm seus próprios
# contratos funcionais verificados nos testes test_*_requires_valid_
# authentication_now (401 sem token) e test_*_rate_limit_enforced_
# with_valid_authentication (200 com token válido).
def test_requests_below_limit_keep_previous_functional_behavior():
    for name in _ENDPOINTS:
        results = _run_probe([_step(name)])
        assert results[0]["status"] == 200, (name, results)


# G) a implementação não usa backend/app/utils/rate_limit.py nem cria
# novas chaves em _BUCKETS -- confirmado inspecionando o estado do
# limiter artesanal após bater nos 7 endpoints repetidamente.
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
