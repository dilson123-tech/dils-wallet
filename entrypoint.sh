#!/bin/sh
set -eu

echo "[BOOT] date: $(date)"
echo "[BOOT] whoami: $(whoami)"
echo "[BOOT] env PORT='$PORT'  (default se vazio -> 8080)"
PORT_USE="${PORT:-8080}"
echo "[BOOT] PORT_USE='$PORT_USE'"

echo "[BOOT] netstat ports (antes de subir):"
# alpine não tem netstat por padrão; tenta ss/nc/lsof, cai pra echo se não tiver
(ss -ltn 2>/dev/null || true) || (netstat -ltn 2>/dev/null || true) || true

echo "[BOOT] testando health local antes do app (vai falhar, é só pra log)"
( wget -qO- "http://127.0.0.1:${PORT_USE}/api/v1/health" || echo "[BOOT] ainda sem app" )

echo "[BOOT] iniciando uvicorn..."
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT_USE}" --log-level debug
