#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-https://dils-wallet-production.up.railway.app}"
USER="${USER:-dilsonpereira231@gmail.com}"
ORIG="${ORIG:-https://aurea-gold-client-production.up.railway.app}"

echo "[1] /healthz"
curl -fsS "$BASE/healthz" >/dev/null

echo "[2] CORS OPTIONS /api/v1/pix/list"
curl -fsSI -X OPTIONS "$BASE/api/v1/pix/list" \
  -H "Origin: $ORIG" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" >/dev/null

echo "[3] PIX fluxo + saldo"
K="smoke-$(date +%s)"
curl -fsS -X POST "$BASE/api/v1/pix/send" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: $USER" \
  -H "X-Idempotency-Key: $K" \
  -d '{"dest":"seed@aurea.local","valor":1.00,"msg":"smoke"}' >/dev/null
curl -fsS "$BASE/api/v1/pix/list" -H "X-User-Email: $USER" >/dev/null
curl -fsS "$BASE/api/v1/pix/saldo" -H "X-User-Email: $USER" >/dev/null
echo "OK"
