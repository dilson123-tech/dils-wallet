#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8090}"

echo "== Aurea Wallet Partner Smoke =="
echo "BASE_URL=$BASE_URL"

echo "-- /healthz --"
health="$(curl -sS --max-time 5 "$BASE_URL/healthz")"
echo "$health" | jq .

wallet_mode="$(echo "$health" | jq -r '.wallet_mode // empty')"
if [ "$wallet_mode" != "demo" ] && [ "$wallet_mode" != "partner" ]; then
  echo "ERRO: wallet_mode inválido ou ausente: $wallet_mode"
  exit 1
fi

echo "-- /api/v1/wallet/partner/status --"
status="$(curl -sS --max-time 5 "$BASE_URL/api/v1/wallet/partner/status")"
echo "$status" | jq .

ok="$(echo "$status" | jq -r '.ok')"
provider="$(echo "$status" | jq -r '.provider // empty')"
real_money="$(echo "$status" | jq -r '.real_money')"

if [ "$ok" != "true" ]; then
  echo "ERRO: partner status ok != true"
  exit 1
fi

if [ -z "$provider" ]; then
  echo "ERRO: provider vazio"
  exit 1
fi

if [ "$wallet_mode" = "demo" ] && [ "$real_money" != "false" ]; then
  echo "ERRO: demo mode não pode ter real_money=true"
  exit 1
fi

echo "WALLET_PARTNER_SMOKE_OK"
