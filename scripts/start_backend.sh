#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8090}"

RUN_DIR="${RUN_DIR:-/tmp/aurea_gold}"
PID_API="${PID_API:-$RUN_DIR/api.pid}"
LOG_API="${LOG_API:-/tmp/aurea_api_${API_PORT}.log}"

BACK_DIR="${BACK_DIR:-$ROOT/backend}"
VENV_ACT="${VENV_ACT:-$ROOT/.venv/bin/activate}"

mkdir -p "$RUN_DIR"

if [[ -f "$PID_API" ]]; then
  pid="$(cat "$PID_API" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "✅ backend já parece rodando (pid=$pid). Use: ./scripts/status.sh"
    exit 0
  fi
  rm -f "$PID_API" || true
fi

# evita porta ocupada
if ss -ltn 2>/dev/null | grep -Eq ":${API_PORT}\\b"; then
  echo "❌ porta $API_PORT já está em uso. Rode: ./scripts/stop_all.sh"
  exit 1
fi

echo "Aurea Gold — START_BACKEND | $(date)"
echo "dir=$BACK_DIR"
echo "log=$LOG_API"

# shellcheck disable=SC1090
source "$VENV_ACT"
cd "$BACK_DIR"

nohup uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" --log-level info >"$LOG_API" 2>&1 &
echo $! > "$PID_API"

sleep 0.4

# health check (melhor esforço)
if command -v curl >/dev/null 2>&1; then
  if curl -sS --max-time 2 "http://127.0.0.1:${API_PORT}/health" >/dev/null; then
    echo "✅ backend up: http://127.0.0.1:${API_PORT}"
  else
    echo "⚠️ backend iniciado mas health ainda não respondeu. Veja: tail -n 50 $LOG_API"
  fi
fi
