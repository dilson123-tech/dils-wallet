#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:8787"
USER="teste@dilswallet.com"
PASS="123456"

j() { jq -r "$1" 2>/dev/null || true; }

echo "== Healthz =="
curl -fsS "$BASE/healthz" && echo -e "\n"

echo "== Tentando login (POST /api/v1/auth/login) =="
LOGIN_RES=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" || true)
echo "$LOGIN_RES" | jq .

TOKEN=$(echo "$LOGIN_RES" | j '.access_token')
if [[ -z "${TOKEN:-}" || "$TOKEN" == "null" ]]; then
  echo -e "\n== Login falhou; tentando registrar e depois logar =="
  REG_RES=$(curl -s -X POST "$BASE/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$USER\",\"password\":\"$PASS\"}" || true)
  echo "$REG_RES" | jq .
  # tenta login novamente
  LOGIN_RES=$(curl -s -X POST "$BASE/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" || true)
  echo "$LOGIN_RES" | jq .
  TOKEN=$(echo "$LOGIN_RES" | j '.access_token')
fi

AUTH_HEADER=()
if [[ -n "${TOKEN:-}" && "$TOKEN" != "null" ]]; then
  AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
  echo -e "\nToken obtido. Prosseguindo autenticado."
else
  echo -e "\nSem token. Prosseguindo sem autenticação (pode dar 401/403)."
fi

echo -e "\n== Saldo (GET /api/v1/transactions/balance) =="
curl -s "$BASE/api/v1/transactions/balance" "${AUTH_HEADER[@]}" | jq .

echo -e "\n== Transações paginadas (GET /api/v1/transactions/paged?page=1&page_size=5) =="
curl -s "$BASE/api/v1/transactions/paged?page=1&page_size=5" "${AUTH_HEADER[@]}" | jq .

# NÃO faz transferências nem mutações aqui (smoke só leitura).
# Opcional: endpoint de debug/sentry se existir SENTRY_DSN configurado:
echo -e "\n== Debug Sentry (GET /debug-sentry) =="
curl -i -s "$BASE/debug-sentry" "${AUTH_HEADER[@]}" | head -n 15
