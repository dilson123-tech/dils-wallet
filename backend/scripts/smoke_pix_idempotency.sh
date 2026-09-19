#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${API_BASE:-}" || -z "${AUREA_USER:-}" || -z "${AUREA_PASS:-}" ]]; then
  echo "[smoke] API_BASE, AUREA_USER e AUREA_PASS são obrigatórios" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[smoke] jq é obrigatório" >&2
  exit 3
fi

LOGIN_BODY="$(mktemp)"
FIRST_BODY="$(mktemp)"
REPLAY_BODY="$(mktemp)"
SUMMARY_BODY="$(mktemp)"
trap 'rm -f "$LOGIN_BODY" "$FIRST_BODY" "$REPLAY_BODY" "$SUMMARY_BODY"' EXIT

LOGIN_PAYLOAD="$(jq -n --arg username "$AUREA_USER" --arg password "$AUREA_PASS" \
  '{username: $username, password: $password}')"

login_status="$(curl -sS -o "$LOGIN_BODY" -w '%{http_code}' -X POST \
  "$API_BASE/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$LOGIN_PAYLOAD")" || {
    echo "[smoke] login falhou" >&2
    exit 10
  }

if [[ "$login_status" != "200" ]]; then
  echo "[smoke] login retornou HTTP $login_status" >&2
  exit 11
fi

TOKEN="$(jq -er '.access_token | strings | select(length > 0)' "$LOGIN_BODY")" || {
  echo "[smoke] login sem access_token válido" >&2
  exit 12
}

BODY='{"valor": 10.00, "chave_pix": "smoke-health-check"}'
KEY="$(uuidgen || cat /proc/sys/kernel/random/uuid)"

echo "[smoke] usando API_BASE=$API_BASE"

first_status="$(curl -sS -o "$FIRST_BODY" -w '%{http_code}' -X POST "$API_BASE/api/v1/pix/send" \
  -H 'Content-Type: application/json' -H "Idempotency-Key: $KEY" \
  -H "Authorization: Bearer $TOKEN" -d "$BODY")" || {
    echo "[smoke] primeira chamada falhou" >&2
    exit 13
  }

if [[ "$first_status" != "200" ]]; then
  echo "[smoke] primeira chamada retornou HTTP $first_status" >&2
  exit 14
fi

sleep 0.3

replay_status="$(curl -sS -o "$REPLAY_BODY" -w '%{http_code}' -X POST "$API_BASE/api/v1/pix/send" \
  -H 'Content-Type: application/json' -H "Idempotency-Key: $KEY" \
  -H "Authorization: Bearer $TOKEN" -d "$BODY")" || {
    echo "[smoke] replay falhou" >&2
    exit 15
  }

if [[ "$replay_status" != "200" ]]; then
  echo "[smoke] replay retornou HTTP $replay_status" >&2
  exit 16
fi

id1="$(jq -er '.id // empty' "$FIRST_BODY")" || {
  echo "[smoke] primeira resposta inválida (sem .id)" >&2
  exit 17
}
id2="$(jq -er '.id // empty' "$REPLAY_BODY")" || {
  echo "[smoke] replay inválido (sem .id)" >&2
  exit 18
}

if [[ "$id1" != "$id2" ]]; then
  echo "[smoke] FALHA: idempotência quebrou" >&2
  exit 19
fi

summary_status="$(curl -sS -o "$SUMMARY_BODY" -w '%{http_code}' \
  -H "Authorization: Bearer $TOKEN" "$API_BASE/api/v1/ai/summary")" || {
    echo "[smoke] summary falhou" >&2
    exit 20
  }

if [[ "$summary_status" != "200" ]]; then
  echo "[smoke] summary retornou HTTP $summary_status" >&2
  exit 21
fi

jq empty "$SUMMARY_BODY" >/dev/null || {
  echo "[smoke] summary inválido" >&2
  exit 22
}

echo "[smoke] OK ✅ idempotência garantida (id=$id1) e summary responde."
