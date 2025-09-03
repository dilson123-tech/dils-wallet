#!/usr/bin/env bash
set -euo pipefail
BASE=${BASE:-http://127.0.0.1:8686}

echo "[1/7] health"
curl -fsS -i "$BASE/healthz" >/dev/null && echo "ok"

echo "[2/7] login (ou registra se 401)"
LOGIN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=teste@dilswallet.com&password=123456')
TOKEN=$(jq -r '.access_token // empty' <<<"$LOGIN")
if [ -z "${TOKEN:-}" ]; then
  curl -fsS -i -X POST "$BASE/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"teste@dilswallet.com","password":"123456"}' >/dev/null
  TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d 'username=teste@dilswallet.com&password=123456' | jq -r '.access_token')
fi
echo "token: ${TOKEN:0:10}..."

echo "[3/7] cria depósito"
curl -fsS -i -X POST "$BASE/api/v1/transactions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tipo":"deposito","valor":10.00,"referencia":"smoke-dep"}' >/dev/null && echo "ok"

echo "[4/7] cria saque"
curl -fsS -i -X POST "$BASE/api/v1/transactions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tipo":"saque","valor":5.00,"referencia":"smoke-saq"}' >/dev/null && echo "ok"

echo "[5/7] lista (top 5)"
curl -fsS "$BASE/api/v1/transactions" -H "Authorization: Bearer $TOKEN" | jq '.[0:5]'

echo "[6/7] saldo"
curl -fsS "$BASE/api/v1/transactions/balance" -H "Authorization: Bearer $TOKEN" | jq

echo "[7/7] negativa (espera 400)"
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$BASE/api/v1/transactions" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"tipo":"deposito","valor":-1,"referencia":"invalid"}' | grep -q '^400$' && echo "ok (400)"
echo "SMOKE: PASS"
