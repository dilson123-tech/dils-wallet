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

if [[ -n "${HEALTH_TOKEN:-}" ]]; then
  say "Ping /healthz"
  HEALTH_CODE=$(curl -s -o /tmp/health.json -w "%{http_code}" \
    -H "X-Health-Token: $HEALTH_TOKEN" \
    "$BASE/healthz")
  cat /tmp/health.json || true
  [[ "$HEALTH_CODE" == "200" ]] || fail "Healthz FAIL ($HEALTH_CODE)"
  ok "Healthz OK"
else
  warn "HEALTH_TOKEN ausente; pulando /healthz no smoke read-only"
fi

say "Login → access token"
LOGIN_CODE=$(curl -s -o /tmp/login.json -w "%{http_code}" \
  -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$EMAIL\",\"password\":\"$PASS\"}")
[[ "$LOGIN_CODE" == "200" ]] || fail "Login FAIL ($LOGIN_CODE): $(cat /tmp/login.json)"
ACCESS=$(jq -r '.access_token // .access // empty' /tmp/login.json)
[[ -n "${ACCESS:-}" ]] || fail "Sem access_token"
ok "Token OK"

AUTH=(-H "Authorization: Bearer $ACCESS")

say "Sanity /users/me"
ME_CODE=$(curl -s -o /tmp/me.json -w "%{http_code}" "$BASE/api/v1/users/me" "${AUTH[@]}")
[[ "$ME_CODE" == "200" ]] || fail "/users/me FAIL ($ME_CODE): $(cat /tmp/me.json)"
jq -r '.email // empty' /tmp/me.json | grep -q "$EMAIL" || fail "Email diferente em /users/me"
ok "users/me OK"

say "DB /users/test-db"
DB_CODE=$(curl -s -o /tmp/db.json -w "%{http_code}" "$BASE/api/v1/users/test-db")
[[ "$DB_CODE" == "200" ]] || fail "/users/test-db FAIL ($DB_CODE): $(cat /tmp/db.json)"
ok "test-db OK"

say "Listar /transactions (somente leitura)"
LIST_CODE=$(curl -s -o /tmp/tx_list.json -w "%{http_code}" "$BASE/api/v1/transactions" "${AUTH[@]}")
[[ "$LIST_CODE" == "200" ]] || fail "GET /transactions FAIL ($LIST_CODE): $(cat /tmp/tx_list.json)"
COUNT=$(jq 'length' /tmp/tx_list.json 2>/dev/null || echo "N/A")
ok "List OK (total=$COUNT)"

printf "\n%s\n" "✔ Smoke READ-ONLY finalizado 🎯"
