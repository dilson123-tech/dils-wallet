#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8090}"
LOGIN_USER="${LOGIN_USER:-customer}"
LOGIN_PASS="${LOGIN_PASS:-dev}"

echo "[smoke] base=$BASE"

# 1) OpenAPI
code="$(curl --max-time 5 -sS -o /dev/null -w "%{http_code}" "$BASE/openapi.json" || true)"
echo "[smoke] openapi http=$code"
[[ "$code" == "200" ]] || { echo "[smoke] FAIL: openapi"; exit 1; }

# 2) Login
AT="$(curl --max-time 5 -fsS -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$LOGIN_USER\",\"password\":\"$LOGIN_PASS\"}" | jq -r '.access_token')"

[[ -n "$AT" && "$AT" != "null" ]] || { echo "[smoke] FAIL: token vazio"; exit 1; }
echo "[smoke] token ok"

# 3) Rate limit (11a deve ser 429)
BODY='{"chave_pix":"teste-chave-pix-123","valor":1.00,"descricao":"smoke-rate-limit"}'

last=""
for i in $(seq 1 11); do
  last="$(curl --ipv4 --max-time 5 -sS -o /dev/null -w "%{http_code}" \
    -X POST "$BASE/api/v1/pix/send" \
    -H "Authorization: Bearer $AT" \
    -H "Content-Type: application/json" \
    -d "$BODY" || echo "000")"
  echo "[smoke] $i -> $last"
done

[[ "$last" == "429" ]] || { echo "[smoke] FAIL: esperado 429 na 11a, veio $last"; exit 1; }
echo "[smoke] OK"
