#!/usr/bin/env bash
set -a
[ -f .env ] && . ./.env
set +a

set -euo pipefail

echo "[AUREA] Boot de produção iniciando..."

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"

# Porta real do ambiente (Railway define $PORT)
PORT="${PORT:-${RAILWAY_TCP_PROXY_PORT:-8080}}"
echo "[AUREA] Porta final detectada: ${PORT}"

# Sobe direto no PORT (sem socat)
echo "[BOOT] init_db..."
python -m app.utils.init_db
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
