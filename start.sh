#!/usr/bin/env sh
set -e
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
