#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
echo "[AUREA START] Bootando Uvicorn na porta ${PORT} (backend/app/main.py)"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
