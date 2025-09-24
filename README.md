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

