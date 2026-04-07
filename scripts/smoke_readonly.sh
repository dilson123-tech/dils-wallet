#!/usr/bin/env bash
set -euo pipefail

BASE="${SMOKE_BASE:-https://dils-wallet-production.up.railway.app}"
EMAIL="${EMAIL:-smoke@dilswallet.com}"
PASS="${PASS:-123456}"
HEALTH_TOKEN="${HEALTH_TOKEN:-}"

say(){ printf "\n▶ %s\n" "$*"; }
ok(){ printf "✔ %s\n" "$*"; }
warn(){ printf "⚠ %s\n" "$*\n"; }
fail(){ printf "✖ %s\n" "$*\n"; exit 1; }

say "OpenAPI"
OPENAPI_CODE=$(curl --max-time 10 -sS -o /tmp/openapi.json -w "%{http_code}" "$BASE/openapi.json" || true)
[[ "$OPENAPI_CODE" == "200" ]] || fail "OpenAPI FAIL ($OPENAPI_CODE)"
ok "OpenAPI OK"

if [[ -n "${HEALTH_TOKEN:-}" ]]; then
  say "Healthz"
  HEALTH_CODE=$(curl --max-time 10 -sS -o /tmp/health.json -w "%{http_code}" \
    -H "X-Health-Token: $HEALTH_TOKEN" \
    "$BASE/healthz" || true)
  [[ "$HEALTH_CODE" == "200" ]] || fail "Healthz FAIL ($HEALTH_CODE)"
  ok "Healthz OK"
else
  warn "HEALTH_TOKEN ausente; pulando /healthz"
fi

say "Login JSON"
LOGIN_CODE=$(curl --max-time 10 -sS -o /tmp/login.json -w "%{http_code}" \
  -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$EMAIL\",\"password\":\"$PASS\"}" || true)
[[ "$LOGIN_CODE" == "200" ]] || fail "Login FAIL ($LOGIN_CODE): $(cat /tmp/login.json)"
ACCESS=$(jq -r '.access_token // .access // empty' /tmp/login.json)
[[ -n "${ACCESS:-}" && "${ACCESS:-}" != "null" ]] || fail "Sem access_token"
ok "Token OK"

printf "\n%s\n" "✔ Smoke READ-ONLY finalizado 🎯"
