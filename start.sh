#!/usr/bin/env sh
set -euxo pipefail

echo "=== env ==="
echo "PWD=$(pwd)  USER=$(id -u -n)  PY=$(python3 -V)"
echo "PORT=${PORT:-unset}"

echo "=== tree /app ==="; ls -la /app || true
echo "=== tree /app/backend ==="; ls -la /app/backend || true

echo "=== preflight imports ==="
python3 - <<'PY'
import importlib, traceback
mods = [
    "backend.app.main",
    "backend.app.database",
    "backend.app.models",
    "backend.app.api.v1.routes.auth",
]
ok=True
for m in mods:
    try:
        importlib.import_module(m)
        print("IMPORT_OK", m)
    except Exception as e:
        print("IMPORT_FAIL", m, "->", repr(e))
        traceback.print_exc()
        ok=False
if not ok:
    raise SystemExit(1)
PY

PORT="${PORT:-8080}"

echo "=== start uvicorn (bg) ==="
python3 -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port "${PORT}" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --log-level debug \
  --lifespan off &
UVICORN_PID=$!
echo "UVICORN_PID=${UVICORN_PID}"

echo "=== smoke: wait app ==="
# espera até o socket abrir (máx ~30s)
for i in $(seq 1 60); do
  if curl -sSf "http://127.0.0.1:${PORT}/openapi.json" >/dev/null 2>&1; then
    echo "openapi OK na tentativa ${i}"
    break
  fi
  sleep 0.5
done

echo "=== probe /openapi.json ==="
curl -i --max-time 5 "http://127.0.0.1:${PORT}/openapi.json" | sed -n '1,40p' || true

echo "=== probe /api/v1/health ==="
curl -i --max-time 5 "http://127.0.0.1:${PORT}/api/v1/health" | sed -n '1,80p' || true

echo "=== handover: foreground ==="
# mantém o container atrelado ao uvicorn
wait ${UVICORN_PID}
