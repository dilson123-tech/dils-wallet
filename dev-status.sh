#!/usr/bin/env bash
set -euo pipefail

HOST_IP="${HOST_IP:-192.168.1.20}"
BE_PORT="${BE_PORT:-8000}"
FE_PORT="${FE_PORT:-5174}"
USER="${AUREA_USER:-user@example.com}"
PASS="${AUREA_PASS:-}"

if [ -z "$AUREA_USER" ] || [ -z "$AUREA_PASS" ]; then
  echo "❌ AUREA_USER/AUREA_PASS não setados. Rode: set -a; source ~/.config/aurea/dev.env; set +a"
  exit 1
fi

ok()   { echo "✅ $*"; }
warn() { echo "⚠️  $*"; }
bad()  { echo "❌ $*"; }

echo "=== AUREA DEV STATUS (LAN) ==="
echo "HOST_IP=${HOST_IP}  BE=${BE_PORT}  FE=${FE_PORT}"
echo

echo "[1] Portas:"
ss -lntp | rg ":(${BE_PORT}|${FE_PORT})\b" && ok "Portas ouvindo" || warn "Uma ou mais portas não estão ouvindo"

echo
echo "[2] Backend /health:"
if curl -sS --max-time 2 "http://127.0.0.1:${BE_PORT}/health" >/dev/null; then
  ok "Backend responde em 127.0.0.1:${BE_PORT}"
else
  bad "Backend não responde em 127.0.0.1:${BE_PORT}"
fi

echo
echo "[3] Front (LAN) responde?"
if curl -sS --max-time 2 "http://127.0.0.1:${FE_PORT}/" >/dev/null; then
  ok "Front responde em 127.0.0.1:${FE_PORT}"
else
  warn "Front não respondeu em 127.0.0.1:${FE_PORT}"
fi

echo
echo "[4] CORS preflight (Origin LAN -> backend):"
code="$(curl -sS -o /tmp/aurea_cors.txt -w '%{http_code}' -X OPTIONS "http://127.0.0.1:${BE_PORT}/api/v1/auth/login" \
  -H "Origin: http://${HOST_IP}:${FE_PORT}" \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type,authorization' || true)"
if [ "${code}" = "200" ] || [ "${code}" = "204" ]; then
  ok "CORS OK (HTTP ${code})"
else
  bad "CORS falhou (HTTP ${code}) — resposta: $(tail -n 1 /tmp/aurea_cors.txt || true)"
fi

echo
echo "[5] Login (gera token curto p/ teste):"
TOKEN="$(curl -sS --max-time 6 "http://127.0.0.1:${BE_PORT}/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"${USER}\",\"password\":\"${PASS}\"}" | jq -r '.access_token' || true)"

if [ -n "${TOKEN}" ] && [ "${TOKEN}" != "null" ] && [ "$(echo "${TOKEN}" | tr '.' '\n' | wc -l | tr -d ' ')" = "3" ]; then
  ok "Token OK (len=${#TOKEN})"
else
  bad "Falha no login/token"
  exit 1
fi

echo
echo "[6] PIX balance (auth):"
bcode="$(curl -sS -o /tmp/aurea_balance.json -w '%{http_code}' --max-time 6 \
  "http://127.0.0.1:${BE_PORT}/api/v1/pix/balance?days=7" \
  -H "Authorization: Bearer ${TOKEN}" || true)"

if [ "${bcode}" = "200" ]; then
  ok "Balance OK"
  jq '{saldo, entradas_mes, saidas_mes, ultimos_7d_len:(.ultimos_7d|length)}' /tmp/aurea_balance.json 2>/dev/null || true
else
  bad "Balance falhou (HTTP ${bcode})"
  tail -n 2 /tmp/aurea_balance.json || true
fi

echo
echo "[7] Forecast (auth):"
fcode="$(curl -sS -o /tmp/aurea_forecast.json -w '%{http_code}' --max-time 6 \
  "http://127.0.0.1:${BE_PORT}/api/v1/pix/forecast" \
  -H "Authorization: Bearer ${TOKEN}" || true)"

if [ "${fcode}" = "200" ]; then
  ok "Forecast OK"
  jq '{saldo_atual, saldo_previsto, status}' /tmp/aurea_forecast.json 2>/dev/null || true
else
  warn "Forecast falhou (HTTP ${fcode})"
  tail -n 2 /tmp/aurea_forecast.json || true
fi

echo
ok "Status final: checks executados."
echo "Links:"
echo " - Backend: http://${HOST_IP}:${BE_PORT}/docs"
echo " - Front:   http://${HOST_IP}:${FE_PORT}/?v=$(date +%s)"
