#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:5178}"
for p in / /login /admin/users; do
  echo "→ testando $BASE$p"
  code=$(curl -s -o /tmp/h -w '%{http_code}' "$BASE$p")
  if [ "$code" != "200" ]; then
    echo "FAIL $BASE$p -> $code"; exit 1
  fi
  grep -q '<div id="root">' /tmp/h && echo "OK  $BASE$p" || { echo "FAIL: index não servido"; exit 1; }
done
echo "✅ SPA fallback OK em $BASE"
