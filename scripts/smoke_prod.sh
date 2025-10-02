#!/usr/bin/env bash
set -euo pipefail

BASE="https://dils-wallet-production.up.railway.app"
USER="teste10@dilswallet.com"
PASS="123456"

echo "== Health =="
curl -sf "$BASE/api/v1/health" | python3 -m json.tool

echo
echo "== Login =="
LOGIN_JSON="$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USER&password=$PASS")"
echo "$LOGIN_JSON" | python3 -m json.tool

# exporta pro ambiente pra facilitar parsing no Python
export LOGIN_JSON

ACCESS=$(python3 - <<'PY'
import os,json
j=json.loads(os.environ["LOGIN_JSON"])
print(j.get("access_token",""))
PY
)

REFRESH=$(python3 - <<'PY'
import os,json
j=json.loads(os.environ["LOGIN_JSON"])
print(j.get("refresh_token",""))
PY
)

echo
echo "ACCESS(short)=${ACCESS:0:32}..."
echo "REFRESH(short)=${REFRESH:0:32}..."

echo
echo "== /users/me (access) =="
curl -s "$BASE/api/v1/users/me" -H "Authorization: Bearer $ACCESS" | python3 -m json.tool

echo
echo "== Refresh =="
NEW_ACCESS=$(curl -s -X POST "$BASE/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH\"}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')

echo "NEW_ACCESS(short)=${NEW_ACCESS:0:32}..."

echo
echo "== /users/me (new_access) =="
curl -s "$BASE/api/v1/users/me" -H "Authorization: Bearer $NEW_ACCESS" | python3 -m json.tool

echo
echo "== OK: smoke test finalizado =="
