#!/usr/bin/env bash
set -e

echo "[AUREA START] Inicializando backend em produção..."

export PYTHONUNBUFFERED=1
export PYTHONPATH=/app

echo "[AUREA START] Subindo API na porta ${PORT:-8080}"
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
