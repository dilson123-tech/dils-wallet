"""
Bloco AI Chat auth — testes de CARACTERIZAÇÃO (não de correção) de
POST /api/v1/ai/chat (backend/app/api/v1/routes/ai_chat.py::ai_chat).

Objetivo: documentar com precisão o comportamento ATUAL, real, em
produção, antes de qualquer migração para Depends(require_customer).
Este arquivo NÃO altera nenhum código de produção, NÃO muda o
contrato 200 -> 401 e NÃO toca em chat_lab.py.

Por que precisa de um servidor HTTP real (não basta TestClient/ASGI
in-process): `/chat` não lê o banco diretamente. Ele resolve
saldo/histórico chamando `_get_pix_balance`/`_get_pix_history`, que
por sua vez fazem uma chamada HTTP de verdade (via `urllib.request`)
para `http://127.0.0.1:8000/api/v1/pix/...` -- a MESMA rota `pix.py`
que já usa `Depends(require_customer)`. Um `TestClient` comum não
abre essa porta (é transporte ASGI in-process), então esse caminho
nunca seria exercitado de forma fiel. Este arquivo sobe um servidor
uvicorn real, na porta 8000 (hardcoded na própria `_fetch_internal_json`,
não configurável), rodando numa thread daemon dentro de um subprocess
Python isolado -- mesmo padrão de isolamento de ambiente já usado em
test_dev_seed_router_gate.py e test_pix_send_intent_http_contract.py
(env definido ANTES de importar app.main, DATABASE_URL apontando para
SQLite descartável num diretório temporário, nunca backend/app.db).

Limitação conhecida e aceita: como a porta é hardcoded no código de
produção, este teste só funciona se a porta 8000 local estiver livre
no momento da execução. Se estiver ocupada por outro processo, o
probe falha alto e claro (RuntimeError "live server did not start"),
nunca silenciosamente.

Os 4 cenários pedidos são cobertos com UM único request por cenário,
todos contra o mesmo servidor vivo, reaproveitando dois usuários reais
com transações PIX distintas e verificáveis (valores diferentes por
usuário), usando a intenção "histórico" do endpoint -- é o único ramo
de `/chat` cujo dado final (soma de `valor` das transações reais)
reflete o dado consultado sem passar por chaves que hoje já vêm
zeradas por um mismatch de contrato entre `_build_saldo_reply`
(espera `balance["saldo_atual"]`) e `pix.py::get_balance` (retorna
`balance["saldo"]`) -- esse mismatch é um achado da investigação
read-only anterior, não é alterado aqui.
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
import threading
import time
from datetime import timedelta

import requests
import uvicorn

from app.database import Base, engine, SessionLocal
from app.utils.security import hash_password, create_access_token
from app.models.user_main import User
from app.models.transaction import Transaction
from app.main import app

Base.metadata.create_all(bind=engine)


def make_user_with_transaction(email, valor_recebido):
    db = SessionLocal()
    user = User(email=email, hashed_password=hash_password("test123"), role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(Transaction(user_id=user.id, tipo="recebimento", valor=valor_recebido))
    db.commit()
    db.close()
    return email


email_a = make_user_with_transaction("chat-auth-a@test.local", 111.00)
email_b = make_user_with_transaction("chat-auth-b@test.local", 222.00)

config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
server = uvicorn.Server(config)
server.install_signal_handlers = lambda: None
thread = threading.Thread(target=server.run, daemon=True)
thread.start()

base = "http://127.0.0.1:8000"
up = False
for _ in range(80):
    try:
        requests.get(base + "/", timeout=0.5)
        up = True
        break
    except Exception:
        time.sleep(0.1)
if not up:
    raise RuntimeError("live server did not start on 127.0.0.1:8000")


def login(email):
    r = requests.post(
        base + "/api/v1/auth/login",
        json={"username": email, "password": "test123"},
        timeout=5,
    )
    assert r.status_code == 200, (email, r.status_code, r.text)
    return r.json()["access_token"]


token_a = login(email_a)
token_b = login(email_b)

MSG = {"message": "qual é o meu histórico de pix"}
results = {}


def _chat(headers):
    r = requests.post(base + "/api/v1/ai/chat", json=MSG, headers=headers, timeout=10)
    return r.status_code, r.json().get("reply", "")


# Cenário 1: token do usuário A + X-User-Email do usuário B.
status, reply = _chat({"Authorization": f"Bearer {token_a}", "X-User-Email": email_b})
results["s1_token_a_header_b_status"] = status
results["s1_token_a_header_b_reply"] = reply

# Cenário 2 (inverso): token do usuário B + X-User-Email do usuário A.
status, reply = _chat({"Authorization": f"Bearer {token_b}", "X-User-Email": email_a})
results["s2_token_b_header_a_status"] = status
results["s2_token_b_header_a_reply"] = reply

# Cenário 3: sem Authorization nenhum (só X-User-Email de um usuário real).
status, reply = _chat({"X-User-Email": email_a})
results["s3_no_authorization_status"] = status
results["s3_no_authorization_reply"] = reply

# Cenário 4a: Authorization com JWT assinado e EXPIRADO (5 min no passado),
# ainda com X-User-Email de outro usuário para maximizar a tentativa de bypass.
expired_token = create_access_token({"sub": email_a}, expires_delta=timedelta(minutes=-5))
status, reply = _chat({"Authorization": f"Bearer {expired_token}", "X-User-Email": email_b})
results["s4a_expired_token_status"] = status
results["s4a_expired_token_reply"] = reply

# Cenário 4b: Authorization com token totalmente inválido (não é um JWT).
status, reply = _chat({"Authorization": "Bearer not-a-real-jwt-token", "X-User-Email": email_b})
results["s4b_garbage_token_status"] = status
results["s4b_garbage_token_reply"] = reply

print(json.dumps(results))
"""


@pytest.fixture(scope="module")
def live_chat_results():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["SECRET_KEY"] = "ai-chat-live-auth-characterization-test-secret"
        env["JWT_SECRET"] = env["SECRET_KEY"]
        # Banco descartável isolado, nunca backend/app.db.
        env["DATABASE_URL"] = f"sqlite:///{tmp}/probe.db"

        proc = subprocess.run(
            [sys.executable, "-c", _PROBE_SCRIPT],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
        )

        assert proc.returncode == 0, (
            f"subprocess do live server falhou:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )

        return json.loads(proc.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------
# 1) Token do usuário A + X-User-Email do usuário B: a resposta nunca
# pode conter o dado real de B (R$ 222,00), só o de A (R$ 111,00) ou
# nenhum dado real.
# ---------------------------------------------------------------------
def test_token_a_with_x_user_email_b_never_returns_b_data(live_chat_results):
    status = live_chat_results["s1_token_a_header_b_status"]
    reply = live_chat_results["s1_token_a_header_b_reply"]

    assert status == 200
    assert "222,00" not in reply, "vazou o valor real do usuário B"
    assert "111,00" in reply, "esperava ver o valor real do próprio usuário A (dono do token)"


# ---------------------------------------------------------------------
# 2) Inverso: token do usuário B + X-User-Email do usuário A: a
# resposta nunca pode conter o dado real de A (R$ 111,00).
# ---------------------------------------------------------------------
def test_token_b_with_x_user_email_a_never_returns_a_data(live_chat_results):
    status = live_chat_results["s2_token_b_header_a_status"]
    reply = live_chat_results["s2_token_b_header_a_reply"]

    assert status == 200
    assert "111,00" not in reply, "vazou o valor real do usuário A"
    assert "222,00" in reply, "esperava ver o valor real do próprio usuário B (dono do token)"


# ---------------------------------------------------------------------
# 3) Sem Authorization: documenta o contrato ATUAL -- 200 com resposta
# de fallback, NUNCA 401, e sem nenhum dado real de PIX (nem de A, que
# foi mandado via X-User-Email, nem de B).
# ---------------------------------------------------------------------
def test_no_authorization_current_contract_is_200_with_fallback(live_chat_results):
    status = live_chat_results["s3_no_authorization_status"]
    reply = live_chat_results["s3_no_authorization_reply"]

    assert status == 200, (
        "contrato atual documentado é 200 (não 401) sem Authorization; "
        "se isso mudou, é uma migração intencional de comportamento, não uma regressão deste teste"
    )
    assert "111,00" not in reply
    assert "222,00" not in reply
    assert "não encontrei movimentações" in reply.lower()


# ---------------------------------------------------------------------
# 4) Authorization inválido/expirado: documenta que, mesmo com
# X-User-Email de outro usuário mandado propositalmente, não há
# vazamento de dado real -- nem do dono nominal do token expirado, nem
# do usuário indicado no header.
# ---------------------------------------------------------------------
def test_expired_authorization_no_data_leak(live_chat_results):
    status = live_chat_results["s4a_expired_token_status"]
    reply = live_chat_results["s4a_expired_token_reply"]

    assert status == 200, "contrato atual documentado é 200 mesmo com token expirado"
    assert "111,00" not in reply
    assert "222,00" not in reply


def test_invalid_authorization_no_data_leak(live_chat_results):
    status = live_chat_results["s4b_garbage_token_status"]
    reply = live_chat_results["s4b_garbage_token_reply"]

    assert status == 200, "contrato atual documentado é 200 mesmo com token inválido"
    assert "111,00" not in reply
    assert "222,00" not in reply
