#!/usr/bin/env bash
set -euo pipefail

# defaults (pode sobrescrever)
PORT="${PORT:-8090}"
API_BASE="${API_BASE:-http://127.0.0.1:$PORT}"
AUREA_USER="${AUREA_USER:-user@example.com}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Aurea Gold SMOKE ALL ==="
echo "PORT=$PORT"
echo "API_BASE=$API_BASE"
echo "AUREA_USER=$AUREA_USER"

# 1) subir backend
PORT="$PORT" bash "$ROOT/run_backend.sh"

# 2) aguardar readiness
bash "$ROOT/smoke/wait_http.sh" "$API_BASE/healthz" 20

# 3) rodar auth+pix
API_BASE="$API_BASE" AUREA_USER="$AUREA_USER" bash "$ROOT/smoke/smoke_auth_pix.sh"

echo "✅ SMOKE ALL PASS"
