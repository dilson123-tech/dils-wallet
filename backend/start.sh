#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"   # entra em backend/
export PYTHONPATH="$(pwd):$(pwd)/app:${PYTHONPATH:-}"
PORT="${PORT:-8000}"

echo "[AUREA START] cwd=$(pwd)"
echo "[AUREA START] PYTHONPATH=${PYTHONPATH}"
echo "[AUREA START] Bootando Uvicorn na porta ${PORT} (module app.main:app)"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
