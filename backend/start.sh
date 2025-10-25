#!/usr/bin/env bash
set -euo pipefail

# garante que estamos na pasta backend/ (onde mora a pasta app/)
cd "$(dirname "$0")"
echo "[AUREA START] cwd=$(pwd)"

# garante que o Python encontre o pacote app.* (ex: app.main)
export PYTHONPATH="$(pwd)"
echo "[AUREA START] PYTHONPATH=${PYTHONPATH}"

# porta que o Railway passa
PORT="${PORT:-8080}"
echo "[AUREA START] Subindo uvicorn app.main:app na porta ${PORT}"

# MUITO IMPORTANTE: usar o python da venv criada no build (/opt/venv)
exec /opt/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
