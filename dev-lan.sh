#!/usr/bin/env bash

# --- AUREA SECRETS (local) ---
SECRETS_FILE="${HOME}/.config/aurea/dev.env"
if [ -f "$SECRETS_FILE" ]; then
  set -a
  . "$SECRETS_FILE"
  set +a
fi
AUREA_USER="${AUREA_USER:-}"
AUREA_PASS="${AUREA_PASS:-}"
if [ -z "$AUREA_USER" ]; then read -r -p "AUREA_USER: " AUREA_USER; fi
if [ -z "$AUREA_PASS" ]; then read -r -s -p "AUREA_PASS: " AUREA_PASS; echo; fi
AUREA_PASS="${AUREA_PASS//$'\r'/}"
# --- /AUREA SECRETS (local) ---

set -euo pipefail

HOST_IP="${HOST_IP:-192.168.1.20}"
BE_PORT="${BE_PORT:-8000}"
FE_PORT="${FE_PORT:-5174}"


wait_backend() {
  local url="http://127.0.0.1:${BE_PORT}/health"
  echo "⏳ Aguardando backend em ${url} ..."
  for i in {1..60}; do
    if curl -sS --max-time 1 "$url" >/dev/null 2>&1; then
      echo "✅ Backend ON"
      return 0
    fi
    sleep 0.25
  done
  echo "❌ Backend não subiu a tempo. Veja: /tmp/aurea_backend.log"
  return 1
}


echo "🧨 Matando portas presas..."
fuser -k "${FE_PORT}/tcp" "${BE_PORT}/tcp" 2>/dev/null || true

echo "✅ Subindo BACKEND (LAN) ..."
cd "$HOME/dils-wallet/backend"
# ativa venv se existir
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

# sobe backend em background
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port "${BE_PORT}" --reload >/tmp/aurea_backend.log 2>&1 &
sleep 1

wait_backend

echo "🔐 Gerando VITE_DEV_TOKEN..."
TOKEN="$(curl -sS --max-time 8 "http://127.0.0.1:${BE_PORT}/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg u "$AUREA_USER" --arg p "$AUREA_PASS" '{username:$u,password:$p}')" | jq -r '.access_token')"

if [ -z "${TOKEN}" ] || [ "${TOKEN}" = "null" ]; then
  echo "❌ Falhou gerar token. Veja /tmp/aurea_backend.log"
  exit 1
fi

echo "✅ Subindo FRONT (LAN) ..."
cd "$HOME/dils-wallet/aurea-gold-client"
export VITE_API_BASE="http://${HOST_IP}:${BE_PORT}"
export VITE_DEV_TOKEN="${TOKEN}"

nohup npm run dev -- --host 0.0.0.0 --port "${FE_PORT}" --strictPort >/tmp/aurea_front.log 2>&1 &
sleep 1

echo ""
echo "✅ LINKS:"
echo "Backend health:  http://${HOST_IP}:${BE_PORT}/health"
echo "Backend docs:    http://${HOST_IP}:${BE_PORT}/docs"
echo "Front (PC):      http://localhost:${FE_PORT}/"
echo "Front (LAN):     http://${HOST_IP}:${FE_PORT}/?v=$(date +%s)"
echo ""
echo "📄 Logs:"
echo " - Backend: /tmp/aurea_backend.log"
echo " - Front:   /tmp/aurea_front.log"
