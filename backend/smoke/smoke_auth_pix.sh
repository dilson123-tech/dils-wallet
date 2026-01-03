#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
USER="${AUREA_USER:-user@example.com}"
PASS="${AUREA_PASS:-}"
[ -n "$PASS" ] || { echo "❌ AUREA_PASS não setada (use dev.env)"; exit 1; }
DAYS="${DAYS:-7}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "❌ Falta comando: $1"; exit 2; }; }
need curl
need jq

echo "== Aurea Gold Smoke (AUTH + PIX) =="
echo "API_BASE: $API_BASE"
echo "USER:     $USER"
echo "DAYS:     $DAYS"
echo

echo "[1/2] Login..."
LOGIN_JSON="$(curl -sS --max-time 10 \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" \
  "$API_BASE/api/v1/auth/login")"

TOKEN="$(echo "$LOGIN_JSON" | jq -r '.access_token // empty')"
if [[ -z "${TOKEN:-}" || "$TOKEN" == "null" ]]; then
  echo "❌ Login NÃO retornou access_token."
  echo "Resposta:"
  echo "$LOGIN_JSON" | jq .
  exit 1
fi
echo "✅ Token OK (len=${#TOKEN})"
echo

echo "[2/2] PIX Balance..."
RID_HDR="/tmp/aurea_rid.hdr"
HTTP_CODE="$(curl -sS --max-time 10 -D "$RID_HDR" -o /tmp/aurea_balance.json -w '%{http_code}' \
  -H "Authorization: Bearer $TOKEN" \
  "$API_BASE/api/v1/pix/balance?days=$DAYS")"

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "❌ FAIL: /pix/balance HTTP $HTTP_CODE"
  echo "Body:"
  cat /tmp/aurea_balance.json | jq . || cat /tmp/aurea_balance.json
  exit 1
fi

RID="$(rg -i "^x-request-id:" "$RID_HDR" | head -n1 | cut -d":" -f2- | xargs || true)"
echo "✅ PASS: /pix/balance HTTP 200 (rid=${RID:-?})"
cat /tmp/aurea_balance.json | jq '{saldo, entradas_mes, saidas_mes, ultimos_7d_len: (.ultimos_7d|length)}'
