#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# DB absoluto (padrão): /home/.../backend/app.db
DB_FILE="${DB_FILE:-$ROOT/app.db}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$DB_FILE}"

  # acha python robusto (CI pode não ativar venv)
  PYBIN="$(ls -1 "$ROOT/.venv/bin/python" "$ROOT/../.venv/bin/python" 2>/dev/null | head -n1 || true)"
  if [ -z "${PYBIN:-}" ]; then
    PYBIN="$(command -v python3 || command -v python || true)"
  fi
  [ -z "${PYBIN:-}" ] && { echo "✖ python não encontrado"; exit 1; }

  # roda uvicorn via módulo (não depende do binário uvicorn estar no PATH)
  UV_CMD=("$PYBIN" -m uvicorn)


# mata quem já estiver na porta
OLD_PID="$(ss -ltnp 2>/dev/null | grep -E ":${PORT}\b" | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"
if [ -n "${OLD_PID:-}" ]; then
  echo "Killing old :$PORT PID=$OLD_PID"
  kill -TERM "$OLD_PID" 2>/dev/null || true
  sleep 0.6
fi

cd "$ROOT"
nohup "${UV_CMD[@]}" app.main:app --host 0.0.0.0 --port "$PORT" > ".uvicorn${PORT}.log" 2>&1 &

  # espera subir (até ~5s) e captura PID
  PID=""
  for _ in $(seq 1 20); do
    PID="$(ss -ltnp 2>/dev/null | grep -E ":${PORT}\b" | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"
    [ -n "${PID:-}" ] && break
    sleep 0.25
  done
  echo "✅ UP: port=$PORT pid=${PID:-?} db=${DATABASE_URL}"

  if [ -z "${PID:-}" ]; then
    echo "✖ Backend não subiu na porta :$PORT"
    echo "--- last 160 lines (.uvicorn${PORT}.log) ---"
    tail -n 160 ".uvicorn${PORT}.log" || true
    exit 1
  fi

# sanity: mostra env do processo (se achar PID)
if [ -n "${PID:-}" ] && [ -r "/proc/$PID/environ" ]; then
  tr '\0' '\n' < "/proc/$PID/environ" | grep -E '^DATABASE_URL=' || true
  readlink "/proc/$PID/cwd" || true
fi
