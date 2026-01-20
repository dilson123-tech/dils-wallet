#!/usr/bin/env bash
set -euo pipefail

API_PORT="${API_PORT:-8090}"
FRONT_PORT="${FRONT_PORT:-5173}"

RUN_DIR="${RUN_DIR:-/tmp/aurea_gold}"
PID_API="${PID_API:-$RUN_DIR/api.pid}"
PID_FRONT="${PID_FRONT:-$RUN_DIR/front.pid}"

kill_pidfile () {
  local name="$1" pidfile="$2"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [[ -n "${pid}" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "⛔ parando $name pid=$pid ..."
      kill -TERM "$pid" 2>/dev/null || true
      for _ in {1..20}; do
        if kill -0 "$pid" 2>/dev/null; then sleep 0.1; else break; fi
      done
      if kill -0 "$pid" 2>/dev/null; then
        echo "⚠️ $name ainda vivo, SIGKILL..."
        kill -KILL "$pid" 2>/dev/null || true
      fi
    else
      echo "⚠️ pidfile de $name existe mas pid não vive ($pidfile)"
    fi
    rm -f "$pidfile" || true
  else
    echo "— $name: sem pidfile"
  fi
}

kill_by_port () {
  local port="$1"
  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "⛔ matando quem tá escutando na porta $port: $pids"
    kill -TERM $pids 2>/dev/null || true
    sleep 0.2
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    [[ -z "$pids" ]] || kill -KILL $pids 2>/dev/null || true
  else
    echo "— porta $port: livre"
  fi
}

mkdir -p "$RUN_DIR"

echo "Aurea Gold — STOP_ALL | $(date)"
kill_pidfile "api" "$PID_API"
kill_pidfile "front" "$PID_FRONT"

# fallback por porta (caso pidfile não exista)
command -v lsof >/dev/null 2>&1 || { echo "⚠️ lsof não instalado; pulando kill por porta"; exit 0; }
kill_by_port "$API_PORT"
kill_by_port "$FRONT_PORT"

echo "✅ stop_all finalizado"
