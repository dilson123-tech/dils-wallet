#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"   # entra na pasta backend
export PYTHONPATH="$(pwd)"   # força o Python a enxergar app.main

PORT="${PORT:-8000}"

echo "[AUREA START] cwd=$(pwd)"
echo "[AUREA START] PYTHONPATH=$PYTHONPATH"
echo "[AUREA START] Subindo uvicorn app.main:app na porta ${PORT}"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
