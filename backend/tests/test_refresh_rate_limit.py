"""
Testes do rate limiting de POST /api/v1/auth/refresh
(backend/app/api/v1/routes/auth.py), reutilizando rl_client_ip/rl_check
já existentes em backend/app/utils/rate_limit.py -- nenhuma dessas
funções foi alterada por esta correção.

Design final (após investigação dedicada de cardinalidade/memória):
SOMENTE bucket por IP (refresh:ip:{ip}). Não existe mais bucket
derivado do refresh token/fingerprint -- foi removido deliberadamente
porque _BUCKETS nunca remove suas próprias chaves, e uma chave
alimentada por qualquer string arbitrária do cliente permitiria
crescimento permanente e não limitado do dicionário.

Todos os cenários que exercitam o endpoint real usam o padrão já
estabelecido neste repositório (test_pix_send_intent_http_contract.py,
test_login_rate_limit_client_ip.py): subprocess Python isolado, com
DATABASE_URL apontando para um SQLite descartável, nunca toca
backend/app.db. Isso também isola _BUCKETS (dicionário em memória, por
processo) entre cenários -- cada subprocess começa com buckets vazios.

Nenhum teste acessa rede externa, nenhum usa banco de Production.
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
import os

from app.database import Base, engine, SessionLocal
from app.utils.security import hash_password
from app.models.user_main import User
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)

db = SessionLocal()
db.add(User(email="refreshtest@test.local", hashed_password=hash_password("correct-password"), role="customer"))
db.commit()
db.close()

client = TestClient(app)

query_log = []
if os.environ.get("PROBE_COUNT_QUERIES") == "1":
    from sqlalchemy import event

    @event.listens_for(engine, "before_cursor_execute")
    def _count(conn, cursor, statement, parameters, context, executemany):
        query_log.append(statement)

report_buckets = os.environ.get("PROBE_REPORT_BUCKETS") == "1"

steps = json.loads(os.environ["PROBE_STEPS"])
results = []
last_refresh_token = None

for step in steps:
    if step["type"] == "login":
        r = client.post(
            "/api/v1/auth/login",
            json={"username": "refreshtest@test.local", "password": "correct-password"},
        )
        if r.status_code == 200:
            last_refresh_token = r.json().get("refresh_token")
        results.append({"status": r.status_code})
        continue

    # step["type"] == "refresh"
    tok = step.get("token")
    if tok == "$last":
        tok = last_refresh_token or ""

    headers = {}
    if step.get("xff") is not None:
        headers["X-Forwarded-For"] = step["xff"]

    before = len(query_log)
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tok}, headers=headers)
    after = len(query_log)

    if r.status_code == 200:
        last_refresh_token = r.json().get("refresh_token")

    results.append({
        "status": r.status_code,
        "retry_after": r.headers.get("retry-after"),
        "queries_during": after - before,
    })

output = {"results": results}
if report_buckets:
    from app.utils.rate_limit import _BUCKETS
    output["bucket_keys"] = sorted(_BUCKETS.keys())

print(json.dumps(output))
"""


def _run_probe(
    steps: list,
    *,
    env_overrides: dict | None = None,
    count_queries: bool = False,
    report_buckets: bool = False,
) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = env.get("SECRET_KEY") or "refresh-rl-test-secret"
        env["JWT_SECRET"] = env.get("JWT_SECRET") or env["SECRET_KEY"]
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"
        env["PROBE_STEPS"] = json.dumps(steps)
        if count_queries:
            env["PROBE_COUNT_QUERIES"] = "1"
        if report_buckets:
            env["PROBE_REPORT_BUCKETS"] = "1"

        # Defaults conservadores para não interferir nos cenários que não
        # tocam explicitamente nesses limites.
        env.setdefault("REFRESH_RL_ENABLED", "1")
        env.setdefault("REFRESH_RL_WINDOW_SEC", "60")
        env.setdefault("REFRESH_RL_MAX_PER_IP", "30")
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


# A) chamada normal (login real -> refresh com o token emitido) não sofre
# regressão causada pelo limiter -- thresholds default, bem acima de 1 uso.
def test_refresh_normal_call_is_not_regressed_by_limiter():
    out = _run_probe([
        {"type": "login"},
        {"type": "refresh", "token": "$last"},
    ])
    results = out["results"]
    assert results[0]["status"] == 200, results
    assert results[1]["status"] == 200, results


# B) vários tokens DIFERENTES do mesmo IP contam para o MESMO bucket-IP
# e atingem 429 -- prova que variar o token não burla a proteção
# volumétrica (não existe mais bucket por token para "escapar" via ele).
def test_different_tokens_same_ip_share_ip_bucket_and_hit_limit():
    steps = [{"type": "refresh", "token": f"invalid-token-{i}"} for i in range(5)]
    out = _run_probe(steps, env_overrides={"REFRESH_RL_MAX_PER_IP": "3"})
    statuses = [r["status"] for r in out["results"]]
    assert statuses[:3] == [401, 401, 401], statuses
    assert 429 in statuses[3:], statuses


# C) o MESMO token repetido também conta para o mesmo bucket-IP (não há
# mais bucket por token para isolar esse cenário -- tudo cai no IP).
def test_same_token_repeated_also_hits_ip_bucket():
    steps = [{"type": "refresh", "token": "same-invalid-token"} for _ in range(5)]
    out = _run_probe(steps, env_overrides={"REFRESH_RL_MAX_PER_IP": "3"})
    statuses = [r["status"] for r in out["results"]]
    assert statuses[:3] == [401, 401, 401], statuses
    assert 429 in statuses[3:], statuses


# D) variar X-Forwarded-For não burla o bucket-IP (reflete a correção do
# PR #249: rl_client_ip usa somente request.client.host, que o
# TestClient mantém constante em todas as chamadas).
def test_varying_xff_does_not_bypass_ip_bucket():
    steps = [
        {"type": "refresh", "token": f"invalid-token-xff-{i}", "xff": f"10.0.0.{i}"}
        for i in range(5)
    ]
    out = _run_probe(steps, env_overrides={"REFRESH_RL_MAX_PER_IP": "3"})
    statuses = [r["status"] for r in out["results"]]
    assert statuses[:3] == [401, 401, 401], statuses
    assert 429 in statuses[3:], statuses


# E) REFRESH_RL_ENABLED=false -> o limiter nunca produz 429, mesmo bem
# acima do limite configurado.
def test_disabled_flag_never_produces_429():
    steps = [{"type": "refresh", "token": f"invalid-token-{i}"} for i in range(8)]
    out = _run_probe(
        steps,
        env_overrides={"REFRESH_RL_ENABLED": "0", "REFRESH_RL_MAX_PER_IP": "2"},
    )
    statuses = [r["status"] for r in out["results"]]
    assert 429 not in statuses, statuses
    assert statuses == [401] * 8, statuses


# F) quando o IP já está bloqueado, nenhum trabalho de banco ocorre.
def test_blocked_request_executes_no_relevant_db_work():
    steps = [
        {"type": "refresh", "token": "token-a"},  # dentro do limite -> faz lookup
        {"type": "refresh", "token": "token-b"},  # bloqueado por IP -> não deveria tocar o banco
    ]
    out = _run_probe(
        steps,
        env_overrides={"REFRESH_RL_MAX_PER_IP": "1"},
        count_queries=True,
    )
    results = out["results"]
    assert results[0]["status"] == 401, results
    assert results[0]["queries_during"] >= 1, results  # chegou a consultar o banco

    assert results[1]["status"] == 429, results
    assert results[1]["queries_during"] == 0, results  # bloqueado antes de qualquer SQL


# G) 429/Retry-After têm comportamento consistente com o padrão já usado
# no /login (header presente, valor numérico em segundos, status 429).
def test_429_has_consistent_retry_after():
    steps = [{"type": "refresh", "token": f"invalid-token-{i}"} for i in range(3)]
    out = _run_probe(steps, env_overrides={"REFRESH_RL_MAX_PER_IP": "2"})
    blocked = [r for r in out["results"] if r["status"] == 429]
    assert blocked, out["results"]
    for r in blocked:
        assert r["retry_after"] is not None, r
        assert int(r["retry_after"]) >= 1, r


# H) não existe mais criação de bucket derivado do refresh token: mesmo
# com N fingerprints distintos, o único prefixo de chave criado em
# _BUCKETS é "refresh:ip:", nunca "refresh:token:".
def test_no_token_derived_bucket_is_ever_created():
    steps = [{"type": "refresh", "token": f"garbage-token-{i}"} for i in range(50)]
    out = _run_probe(
        steps,
        env_overrides={"REFRESH_RL_MAX_PER_IP": "1000"},  # não bloqueia nenhuma tentativa
        report_buckets=True,
    )
    keys = out["bucket_keys"]
    assert keys, "esperava pelo menos a chave do bucket por IP"
    assert all(k.startswith("refresh:ip:") for k in keys), keys
    assert not any(k.startswith("refresh:token:") for k in keys), keys
    # 50 refreshes do mesmo IP -> uma única chave de bucket (por IP),
    # não 50 (o que aconteceria se ainda existisse a dimensão por token).
    assert len(keys) == 1, keys
