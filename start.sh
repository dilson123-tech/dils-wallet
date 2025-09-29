#!/usr/bin/env sh
set -ex

export PYTHONPATH="/app/backend:${PYTHONPATH}"

echo "=== runtime diag ==="
python3 --version
python3 -c "import sys,os; print('CWD=',os.getcwd()); print('PYTHONPATH=',sys.path)"

echo "=== test import ==="
python3 - <<'PY'
import importlib, traceback
try:
    m = importlib.import_module('app.main')
    print('IMPORT_OK=', bool(getattr(m,'app',None)))
except Exception as e:
    print('IMPORT_FAIL:', e); traceback.print_exc(); raise SystemExit(2)
PY

echo "=== starting uvicorn ==="
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --proxy-headers --forwarded-allow-ips="*"
