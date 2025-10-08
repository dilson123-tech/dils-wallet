#!/usr/bin/env bash
set -euo pipefail

# Carrega variáveis se existir .env* (ignora comentários e linhas vazias)
load_env() {
  for f in .env .env.local .env.prod .env.production; do
    [ -f "$f" ] || continue
    # exporta apenas linhas no formato KEY=VAL (sem espaços)
    set -a
    # shellcheck disable=SC1090
    . "$f" || true
    set +a
  done
}
load_env

: "${DATABASE_URL:?DATABASE_URL não definido}"
STAMP=$(date -u +'%Y%m%d-%H%M%SZ')
OUT="backups/db_${STAMP}.sql.gz"

echo "[backup] iniciando dump -> $OUT"
pg_dump "$DATABASE_URL" | gzip -9 > "$OUT"

# manter só os 7 mais recentes
ls -1t backups/db_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "[backup] ok -> $(ls -lh "$OUT" | awk '{print $9" ("$5")"}')"
