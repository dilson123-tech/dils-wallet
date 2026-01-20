#!/usr/bin/env bash
set -euo pipefail
last="$(ls -1 backups | sort | tail -n1)"
test -z "$last" && { echo "Nenhum snapshot em ./backups"; exit 1; }
src="backups/$last"
echo "⏪ Restaurando de $src"

tar -xzf "$src/aurea-backend.tgz" -C .
tar -xzf "$src/aurea-client.tgz"  -C .
( set +e; cp -v "$src"/.env* backend/ 2>/dev/null || true; )
( set +e; cp -v "$src"/.env* aurea-gold-client/ 2>/dev/null || true; )
( set +e; if [ -f "$src/app.db" ]; then cp -v "$src/app.db" backend/app.db; fi )
echo "✅ Restore concluído."
