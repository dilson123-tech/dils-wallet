#!/usr/bin/env sh
set -euxo pipefail

PORT="${PORT:-8080}"
APP="backend.app.main:app"

echo "== container / runtime info =="
date
echo "PWD=$(pwd)"
id || true
uname -a || true

echo "== env (top) =="
env | sort | sed -n '1,120p' || true

echo "== filesystem =="
ls -la /app || true
ls -la /app/backend || true

echo "== python =="
python3 -V || true
python3 - <<'PY' || true
import sys
print("executable:", sys.executable)
try:
    import uvicorn; print("uvicorn:", uvicorn.__version__)
except Exception as e:
    print("uvicorn import FAIL:", repr(e))
PY

echo "== preflight imports =="
python3 - <<'PY' || true
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
        print("OK:", m)
    except Exception as e:
        print("FAIL:", m, "->", repr(e))
        traceback.print_exc()
        ok=False
print("preflight_ok=", ok)
PY

# watcher: tenta bater no openapi local enquanto o uvicorn sobe
(
  for i in $(seq 1 40); do
    sleep 1
    echo "[watch] try $i -> http://127.0.0.1:${PORT}/openapi.json"
    if curl -fsS "http://127.0.0.1:${PORT}/openapi.json" >/dev/null 2>&1; then
      echo "[watch] OK: openapi respondeu"
      break
    fi
  done
) &

echo "== start uvicorn =="
exec python3 -m uvicorn "$APP" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --access-log \
  --log-level info
