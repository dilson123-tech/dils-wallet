![CI](https://github.com/dilson123-tech/dils-wallet/actions/workflows/ci.yml/badge.svg)

# Dils Wallet — MVP

API + UI simples para gerenciar transações (depósito/saque) com autenticação JWT.

## ✅ O que já foi feito
- **Auth:** registro e login (`/api/v1/auth/register`, `/api/v1/auth/login`) com JWT (PyJWT).
- **Usuário:** `/api/v1/users/me`.
- **Transações:** `POST/GET /api/v1/transactions` e `GET /api/v1/transactions/balance`.
- **UI Web:** `/ui` (login, saldo, lista, criar transação, logout).
- **Smoke test:** `./smoke.sh` (health, login/registro, criar/listar, saldo, negativo 400).
- **Higiene:** `healthz`, favicon 204, rotas normalizadas, SECRET_KEY via env.

## ▶️ Como rodar (dev)
**Terminal A (server)**
$ export SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
$ uvicorn app.main:app --host 127.0.0.1 --port 8686 --reload --log-level debug

**Terminal C (sanity)**
$ BASE=http://127.0.0.1:8686
$ curl -i $BASE/healthz

**Login rápido**
$ TOKEN=$(curl -s -X POST $BASE/api/v1/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d 'username=teste@dilswallet.com&password=123456' | jq -r '.access_token')
$ curl -s $BASE/api/v1/users/me -H "Authorization: Bearer $TOKEN" | jq

**UI**
Abra: http://127.0.0.1:8686/ui

## 🔜 Próximos passos
- Transferência (`tipo=transferencia`)
- Paginação na lista
- Testes (pytest) e migrations (Alembic)
- Observabilidade/CI (quando sair do MVP)
 


## Histórico de commits
* 03/09/2025 as 19:44 — push do README e MVP

## Paginação de transações
**Endpoint:** `GET /api/v1/transactions/paged`  
**Query:** `page` (>=1), `page_size` (1..100)  
**Resposta:**
```json
{
  "items": [ /* TransactionResponse[] */ ],
  "meta": {
    "page": 1, "page_size": 5, "total": 10,
    "total_pages": 2, "has_next": true, "has_prev": false
  }
}


\n\n## Paginação de transações
**Endpoint:** `GET /api/v1/transactions/paged`
**Query:** `page` (>=1), `page_size` (1..100)
**Resposta (exemplo):** {\"items\": [...], \"meta\": {\"page\": 1, \"page_size\": 5, \"total\": 10, \"total_pages\": 2, \"has_next\": true, \"has_prev\": false}}

**cURL:**
BASE=http://127.0.0.1:8000
TOKEN=(POST /api/v1/auth/login)
GET /api/v1/transactions/paged?page=1&page_size=5

**UI:** pager em `/ui` (Prev/Next + page size).
