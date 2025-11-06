#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8080}"
BODY='{"valor": 10.00, "dest": "health-check"}'
KEY="$(uuidgen || cat /proc/sys/kernel/random/uuid)"

echo "[smoke] usando API_BASE=$API_BASE"

first="$(curl -sS -X POST "$API_BASE/api/v1/pix/send" \
  -H 'Content-Type: application/json' -H "Idempotency-Key: $KEY" \
  -d "$BODY")" || { echo "[smoke] primeira chamada falhou"; exit 10; }

sleep 0.3

replay="$(curl -sS -X POST "$API_BASE/api/v1/pix/send" \
  -H 'Content-Type: application/json' -H "Idempotency-Key: $KEY" \
  -d "$BODY")" || { echo "[smoke] replay falhou"; exit 11; }

echo "[smoke] first:  $first"
echo "[smoke] replay: $replay"

# exige jq
if ! command -v jq >/dev/null 2>&1; then
  echo "[smoke] instalando jq..."
  if command -v apt-get >/dev/null 2>&1; then sudo apt-get update -y && sudo apt-get install -y jq uuid-runtime; fi
fi

id1="$(echo "$first"  | jq -r '.id // empty')"
id2="$(echo "$replay" | jq -r '.id // empty')"

if [[ -z "$id1" || -z "$id2" ]]; then
  echo "[smoke] respostas inválidas (sem .id)."
  exit 12
fi

if [[ "$id1" != "$id2" ]]; then
  echo "[smoke] FALHA: idempotência quebrou (id1=$id1, id2=$id2)."
  exit 13
fi

# sanity extra: summary responde JSON
curl -sS "$API_BASE/api/v1/ai/summary" | jq . >/dev/null || {
  echo "[smoke] summary inválido"; exit 14; }

echo "[smoke] OK ✅ idempotência garantida (id=$id1) e summary responde."
