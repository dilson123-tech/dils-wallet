#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="$(cd "$ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")"

API_PORT="${API_PORT:-8090}"
FRONT_PORT="${FRONT_PORT:-5173}"

RUN_DIR="${RUN_DIR:-/tmp/aurea_gold}"
PID_API="${PID_API:-$RUN_DIR/api.pid}"
PID_FRONT="${PID_FRONT:-$RUN_DIR/front.pid}"

LOG_API="${LOG_API:-/tmp/aurea_api_${API_PORT}.log}"
LOG_FRONT="${LOG_FRONT:-/tmp/aurea_front_${FRONT_PORT}.log}"

echo "Aurea Gold — STATUS  |  $(date)"
echo "repo=$ROOT"
echo "branch=$BRANCH"
echo

echo "== PORTAS (ss -ltnp) =="
if ss -ltnp 2>/dev/null | grep -Eq "(:${API_PORT}|:${FRONT_PORT})\\b"; then
  ss -ltnp 2>/dev/null | rg ":(?:${API_PORT}|${FRONT_PORT})\\b" || true
else
  echo "ports ${FRONT_PORT}/${API_PORT}: livres ✅"
fi
echo

check_pid () {
  local name="$1" pidfile="$2"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [[ -n "${pid}" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "$name: pid=$pid (vivo) ✅"
      ps -fp "$pid" -o pid,ppid,cmd 2>/dev/null || true
    else
      echo "$name: pidfile existe mas pid não está vivo ⚠️  ($pidfile)"
    fi
  else
    echo "$name: sem pidfile ($pidfile)"
  fi
}

echo "== PROCESSOS (pidfiles) =="
check_pid "api" "$PID_API"
check_pid "front" "$PID_FRONT"
echo

echo "== LOGS (tail) =="
if [[ -f "$LOG_API" ]]; then
  echo "-- api: $LOG_API"
  tail -n 12 "$LOG_API" || true
else
  echo "-- api: (sem log em $LOG_API)"
fi
echo
if [[ -f "$LOG_FRONT" ]]; then
  echo "-- front: $LOG_FRONT"
  tail -n 12 "$LOG_FRONT" || true
else
  echo "-- front: (sem log em $LOG_FRONT)"
fi
echo

ENV_LOCAL="$ROOT/aurea-gold-client/.env.local"
echo "== FRONT .env.local =="
if [[ -f "$ENV_LOCAL" ]]; then
  sed -n '1,50p' "$ENV_LOCAL"
else
  echo "(não existe) — ok se ainda não subiu o front"
fi
