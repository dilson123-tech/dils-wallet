#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-8000}"
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT}"
