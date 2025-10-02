#!/usr/bin/env bash
set -euo pipefail

# Garante que o backend esteja no PYTHONPATH (o Nixpacks já faz isso, mas vamos ser explícitos)
export PYTHONPATH="/app/backend:${PYTHONPATH:-}"

echo "== dils-wallet :: starting uvicorn =="
echo "PYTHONPATH=$PYTHONPATH  PORT=${PORT:-8080}"

# Sobe a API real
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
