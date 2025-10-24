#!/usr/bin/env bash
set -euo pipefail

# Força cwd e caminho raiz dos módulos
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/app"

PORT="${PORT:-8000}"

echo "[AUREA START] cwd=$(pwd)"
echo "[AUREA START] PYTHONPATH=$PYTHONPATH"
echo "[AUREA START] Subindo uvicorn backend.app.main:app na porta ${PORT}"

exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT}"
