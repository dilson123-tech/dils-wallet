#!/usr/bin/env bash
set -euo pipefail

echo "[AUREA] Boot de produção iniciando..."

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"

# detecta porta real
if [ -z "${PORT:-}" ] || [ "${PORT}" = "0" ]; then
  echo "[AUREA][WARN] PORT vazio. Tentando RAILWAY_TCP_PROXY_PORT..."
  PORT="${RAILWAY_TCP_PROXY_PORT:-8080}"
fi

echo "[AUREA] Porta final detectada: ${PORT}"

# inicia uvicorn em background na 8080
/opt/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &

# se PORT != 8080, cria proxy
if [ "${PORT}" != "8080" ]; then
  echo "[AUREA] Criando proxy de ${PORT} → 8080 (socat)..."
  socat TCP-LISTEN:${PORT},reuseaddr,fork TCP:127.0.0.1:8080 &
fi

wait -n
