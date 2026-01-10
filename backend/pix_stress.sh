#!/usr/bin/env bash
set -euo pipefail

API="${API:-http://127.0.0.1:8000}"
USER="${USER:-}"
N="${1:-10}"

if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq não encontrado. Instale: sudo apt-get install -y jq"
  exit 1
fi

if [[ -z "$USER" ]]; then
  echo "❌ Defina USER (email). Ex: USER='seu@email' API='http://192.168.1.20:8000' ./pix_stress.sh 10"
  exit 1
fi

read -rsp "PASS: " PASS; echo

echo "API=$API"
echo "USER=$USER"

# login (pega token e valida)
RESP="$(curl -sS --max-time 8 -w $'\n%{http_code}' \
  "$API/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}")"

BODY="$(echo "$RESP" | sed '$d')"
CODE="$(echo "$RESP" | tail -n1)"

if [[ "$CODE" != "200" ]]; then
  echo "❌ login=$CODE"
  echo "$BODY"
  exit 1
fi

TOKEN="$(echo "$BODY" | jq -r '.access_token // empty')"
if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "❌ token vazio/null"
  echo "$BODY"
  exit 1
fi

echo "✅ login=200 token_len=${#TOKEN}"

uuid() {
  if command -v uuidgen >/dev/null 2>&1; then uuidgen
  else cat /proc/sys/kernel/random/uuid
  fi
}

for i in $(seq 1 "$N"); do
  bcode="$(curl -sS -o /dev/null -w "%{http_code}" --max-time 8 \
    "$API/api/v1/pix/balance?days=7" \
    -H "Authorization: Bearer $TOKEN")"
  echo "balance#$i=$bcode"

  skey="$(uuid)"
  scode="$(curl -sS -o /dev/null -w "%{http_code}" --max-time 8 \
    -X POST "$API/api/v1/pix/send" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-User-Email: $USER" \
    -H "Idempotency-Key: $skey" \
    -d '{"dest":"teste@pix","valor":1,"descricao":"ping"}')"
  echo "send#$i=$scode"
done

unset PASS
