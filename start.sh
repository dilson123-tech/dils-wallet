#!/usr/bin/env sh
set -ex

echo "=== runtime diag ==="
python -V
python -c "import sys,os; print('CWD=',os.getcwd())"
python -c "import importlib, traceback; 
try:
    m = importlib.import_module('backend.app.main'); 
    print('IMPORT_OK=', bool(getattr(m,'app',None)))
except Exception as e:
    print('IMPORT_FAIL:', e); traceback.print_exc(); 
    raise SystemExit(2)
"

echo "=== starting uvicorn ==="
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --proxy-headers --forwarded-allow-ips="*"
