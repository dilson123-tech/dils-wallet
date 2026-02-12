#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
LOGIN_EMAIL="${LOGIN_EMAIL:-dilsonpereira231@gmail.com}"
LOGIN_PASS="${LOGIN_PASS:-Aurea@12345}"
N="${N:-8}"

echo "API_BASE=$API_BASE"
echo "LOGIN_EMAIL=$LOGIN_EMAIL"
echo "N=$N"

# sanity: API viva
curl -fsS --max-time 3 "$API_BASE/openapi.json" >/dev/null || {
  echo "❌ API não responde em $API_BASE"
  echo "👉 tenta: API_BASE=http://192.168.1.20:8000 ./pix_stress.sh"
  exit 1
}

LOGIN_JSON="$(curl -fsS --max-time 6 "$API_BASE/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$LOGIN_EMAIL\",\"password\":\"$LOGIN_PASS\"}")"

TOKEN="$(jq -r '.access_token // empty' <<<"$LOGIN_JSON")"
if [[ -z "$TOKEN" ]]; then
  echo "❌ Login não retornou access_token. Resposta:"
  echo "$LOGIN_JSON" | head -c 400; echo
  exit 1
fi

echo "token_len=${#TOKEN} dots=$(awk -F. '{print NF}' <<<"$TOKEN")"

for i in $(seq 1 "$N"); do
  code="$(curl -sS -o /tmp/pix_balance.json -w '%{http_code}' --max-time 6 \
    "$API_BASE/api/v1/pix/balance?days=7" \
    -H "Authorization: Bearer $TOKEN")"
  echo "balance[$i]=$code"
  [[ "$code" == "200" ]] || { echo "❌ body:"; head -c 400 /tmp/pix_balance.json; echo; exit 1; }
done

echo "✅ stress OK"
