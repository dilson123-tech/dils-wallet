#!/usr/bin/env sh
set -ex
exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --proxy-headers --forwarded-allow-ips="*"
