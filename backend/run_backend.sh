#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# DB absoluto (padrão): /home/.../backend/app.db
DB_FILE="${DB_FILE:-$ROOT/app.db}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$DB_FILE}"

# acha uvicorn
UV="$(ls -1 "$ROOT/.venv/bin/uvicorn" "$ROOT/../.venv/bin/uvicorn" 2>/dev/null | head -n1 || true)"
[ -z "${UV:-}" ] && UV="uvicorn"

# mata quem já estiver na porta
OLD_PID="$(ss -ltnp 2>/dev/null | grep -E ":${PORT}\b" | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"
if [ -n "${OLD_PID:-}" ]; then
  echo "Killing old :$PORT PID=$OLD_PID"
  kill -TERM "$OLD_PID" 2>/dev/null || true
  sleep 0.6
fi

cd "$ROOT"
nohup "$UV" app.main:app --host 0.0.0.0 --port "$PORT" > ".uvicorn${PORT}.log" 2>&1 &

sleep 0.8
PID="$(ss -ltnp 2>/dev/null | grep -E ":${PORT}\b" | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"
echo "✅ UP: port=$PORT pid=${PID:-?} db=${DATABASE_URL}"

# sanity: mostra env do processo (se achar PID)
if [ -n "${PID:-}" ] && [ -r "/proc/$PID/environ" ]; then
  tr '\0' '\n' < "/proc/$PID/environ" | grep -E '^DATABASE_URL=' || true
  readlink "/proc/$PID/cwd" || true
fi
