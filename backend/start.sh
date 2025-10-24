#!/usr/bin/env bash
set -euo pipefail

# entra na pasta backend dentro do container
cd "$(dirname "$0")"

# queremos que Python enxergue 'app' como pacote raiz
# então PYTHONPATH deve ser /app/backend (que contém a pasta app/)
export PYTHONPATH="$(pwd)"

PORT="${PORT:-8000}"

echo "[AUREA START] cwd=$(pwd)"
echo "[AUREA START] PYTHONPATH=$PYTHONPATH"
echo "[AUREA START] Subindo uvicorn app.main:app na porta ${PORT}"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
