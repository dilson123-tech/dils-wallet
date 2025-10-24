#!/usr/bin/env bash
set -euo pipefail

# Força cwd = /app/backend dentro do container Railway
cd "$(dirname "$0")"

# Força o Python a enxergar o pacote "app" aqui dentro
export PYTHONPATH="$(pwd)"

PORT="${PORT:-8000}"

echo "[AUREA START] cwd=$(pwd)"
echo "[AUREA START] PYTHONPATH=$PYTHONPATH"
echo "[AUREA START] Subindo uvicorn app.main:app na porta ${PORT}"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
