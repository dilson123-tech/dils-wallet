#!/usr/bin/env bash
set -euo pipefail

# garante que o cwd é a pasta backend/
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
echo "[AUREA START] Bootando Uvicorn na porta ${PORT} (cwd=$(pwd))"

# importa o módulo relativo à pasta backend/
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
