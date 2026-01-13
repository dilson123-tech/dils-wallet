#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

FRONT_HOST="${FRONT_HOST:-0.0.0.0}"
FRONT_PORT="${FRONT_PORT:-5173}"
API_BASE="${API_BASE:-http://192.168.1.20:8090}"

RUN_DIR="${RUN_DIR:-/tmp/aurea_gold}"
PID_FRONT="${PID_FRONT:-$RUN_DIR/front.pid}"
LOG_FRONT="${LOG_FRONT:-/tmp/aurea_front_${FRONT_PORT}.log}"

FRONT_DIR="${FRONT_DIR:-$ROOT/aurea-gold-client}"
ENV_LOCAL="${ENV_LOCAL:-$FRONT_DIR/.env.local}"

mkdir -p "$RUN_DIR"

if [[ -f "$PID_FRONT" ]]; then
  pid="$(cat "$PID_FRONT" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "✅ front já parece rodando (pid=$pid). Use: ./scripts/status.sh"
    exit 0
  fi
  rm -f "$PID_FRONT" || true
fi

# evita porta ocupada
if ss -ltn 2>/dev/null | grep -Eq ":${FRONT_PORT}\b"; then
  echo "❌ porta $FRONT_PORT já está em uso. Rode: ./scripts/stop_all.sh"
  exit 1
fi

echo "Aurea Gold — START_FRONT | $(date)"
echo "dir=$FRONT_DIR"
echo "api=$API_BASE"
echo "env=$ENV_LOCAL"
echo "log=$LOG_FRONT"

cd "$FRONT_DIR"

# escreve .env.local (fonte única pra Vite)
printf "VITE_API_BASE=%s\n" "$API_BASE" > "$ENV_LOCAL"

nohup npm run dev -- --host "$FRONT_HOST" --port "$FRONT_PORT" >"$LOG_FRONT" 2>&1 &
echo $! > "$PID_FRONT"

sleep 0.6

echo "✅ front iniciado (melhor esforço). Abra:"
echo "   http://127.0.0.1:${FRONT_PORT}"
echo "   http://192.168.1.20:${FRONT_PORT}"
