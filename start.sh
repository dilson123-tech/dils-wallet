#!/usr/bin/env sh
set -eux

PORT="${PORT:-8080}"
APP="backend.app.main:app"

echo "== runtime info =="
date || true
echo "PWD=$(pwd)"
id || true
uname -a || true

echo "== env (top 120) =="
env | sort | sed -n '1,120p' || true

echo "== tree /app =="
ls -la /app || true
ls -la /app/backend || true

echo "== python & deps =="
python3 -V || true
python3 - <<'PY' || true
import sys, importlib
print("executable:", sys.executable)
for m in ("uvicorn","fastapi","starlette"):
    try:
        mod = importlib.import_module(m)
        print(m, "OK", getattr(mod,"__version__", "?"))
    except Exception as e:
        print(m, "FAIL:", repr(e))
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

# watcher sem 'seq' (100% POSIX). Roda em background.
(
  i=0
  while [ "$i" -lt 300 ]; do
    i=$((i+1))
    echo "[watch] try $i -> http://127.0.0.1:${PORT}/openapi.json"
    if curl -fsS "http://127.0.0.1:${PORT}/openapi.json" >/dev/null 2>&1; then
      echo "[watch] OK: openapi respondeu"
      break
    fi
    sleep 1
  done
  if [ "$i" -ge 300 ]; then
    echo "[watch] NUNCA ficou pronto em 300s"
  fi
) &

echo "== start uvicorn on PORT=${PORT} =="
exec python3 -m uvicorn "${APP}" \
  --host 0.0.0.0 \
  --port "${PORT}" \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --access-log \
  --log-level info
