[![Smoke Prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke_prod.yml/badge.svg)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke_prod.yml)

# Dils Wallet — Backend & Frontend

[![smoke-prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke.yml/badge.svg?branch=main)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke.yml)
[![health-prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/health.yml/badge.svg?branch=main)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/health.yml)

API de carteira minimal + front estático simples. Tokens JWT com **login** + **refresh**, CORS habilitado p/ dev local, smoke/health no GitHub Actions e `/healthz` protegido por token.

---

## 🔗 Endpoints (API)
**Base (prod):** `https://dils-wallet-production.up.railway.app`

- `POST /api/v1/auth/register` — `{ "email", "password" }`  
- `POST /api/v1/auth/login` — `Content-Type: application/x-www-form-urlencoded`  
  - body: `username=<email>&password=<senha>`  
  - retorna: `access_token`, `refresh_token`
- `POST /api/v1/auth/refresh` — `Content-Type: application/json`  
  - body: `{ "refresh_token": "<...>" }`  
  - retorna: `access_token` novo
- `GET /api/v1/transactions/balance` — `Authorization: Bearer <access>`  
- `GET /healthz` — **requer** header `X-Health-Token: <token>` (em prod)

---

## 🧪 Curl Snippets úteis

```bash
# Login (x-www-form-urlencoded)
curl -sS -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teste9@dilswallet.com&password=123456"

# Refresh (JSON)
curl -sS -X POST "$BASE/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"<REFRESH>\"}"

# Saldo
curl -sS -H "Authorization: Bearer <ACCESS>" "$BASE/api/v1/transactions/balance"

# Health (prod)
curl -i -H "X-Health-Token: <TOKEN>" "$BASE/healthz"


---

### 🧩 PIX Mock – Histórico e Seed Automático

#### 📜 Endpoints
- `POST /api/v1/pix/pix/mock-transfer` — cria uma transferência PIX simulada com idempotência.  
- `GET /api/v1/pix/history` — retorna o histórico de transferências PIX mock, ordenado por data.

#### 🧠 Modelo Persistido
Tabela: `pix_transactions`
\`\`\`sql
id | from_account_id | to_account_id | amount | created_at
\`\`\`

#### ⚙️ Seed Automático (somente para ambientes vazios)
O sistema pode criar as contas iniciais `1` e `2` automaticamente quando estas não existirem — **apenas** se a variável de ambiente estiver habilitada:

\`\`\`
PIX_MOCK_SEED_ENABLED=true
\`\`\`

> 🔒 **Por padrão**, o seed está **desativado** (`false`).  
> Em produção, mantenha `PIX_MOCK_SEED_ENABLED=false`.  
> Para recriar contas mock em ambientes de teste, ligue temporariamente e execute um `mock-transfer` — as contas serão geradas com saldo inicial seguro (`1000.0` e `100.0`).

#### 🩺 Healthchecks
- `/health` — usado internamente pelo app.  
- `/healthz` — compatibilidade com Railway (`{"status": "ok"}`).

#### ✅ Boas práticas
- Evite usar o seed fora de ambientes de teste.  
- Use idempotência sempre (`Idempotency-Key` único).  
- Para debugging, combine com `pix/history` e `transactions`.

---

### 🧪 Smoke Tests – PIX Mock & Health

Use estes comandos para testar o ambiente local e de produção:

#### 🖥️ Local
```bash
BASE_LOCAL="http://127.0.0.1:8000"
IDEM="pix-local-$(date +%s)"

# Testa mock-transfer
curl -s -X POST "$BASE_LOCAL/api/v1/pix/pix/mock-transfer" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $IDEM" \
  -d "{\"from_account_id\":1,\"to_account_id\":2,\"amount\":3.33,\"idempotency_key\":\"$IDEM\"}" | jq .

# Verifica histórico
curl -s "$BASE_LOCAL/api/v1/pix/history" | jq .

# Healthcheck
curl -s "$BASE_LOCAL/healthz" | jq .

```
