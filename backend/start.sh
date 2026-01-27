#!/usr/bin/env bash
set -euo pipefail

echo "[AUREA] Boot de produção iniciando..."
export PYTHONFAULTHANDLER=1
export PYTHONUNBUFFERED=1

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"

# Porta real do ambiente (Railway define $PORT)
PORT="${PORT:-${RAILWAY_TCP_PROXY_PORT:-8080}}"
echo "[AUREA] Porta final detectada: ${PORT}"

echo "[BOOT] init_db (fail-fast)..."
python -m app.utils.init_db

echo "[BOOT] starting uvicorn app.main:app ..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --log-level debug --access-log
