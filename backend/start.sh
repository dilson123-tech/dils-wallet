#!/usr/bin/env bash
set -euo pipefail

# entrar na pasta backend (dentro do container Railway isso vira /app/backend)
cd "$(dirname "$0")"

# garantir que Python enxerga a pasta backend como raiz dos módulos
export PYTHONPATH="$(pwd)"

PORT="${PORT:-8000}"

echo "[AUREA START] cwd=$(pwd)"
echo "[AUREA START] PYTHONPATH=$PYTHONPATH"
echo "[AUREA START] Subindo uvicorn app.main:app na porta ${PORT}"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
