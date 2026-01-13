#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://192.168.1.20:8090}"
FRONT_BASE="${FRONT_BASE:-http://192.168.1.20:5173}"
LOGIN_EMAIL="${LOGIN_EMAIL:-dilsonpereira231@gmail.com}"

say() { printf "%s\n" "$*"; }
die() { say "❌ $*"; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "Falta '$1' (instale e tente de novo)"; }
need curl
need jq

# sanity: API/Front vivos
curl -sS --max-time 2 "$API_BASE/healthz" >/dev/null 2>&1 || die "API não responde em $API_BASE (tente: API_BASE=... ./scripts/open_panel.sh)"
curl -sS --max-time 2 "$FRONT_BASE" >/dev/null 2>&1 || die "Front não responde em $FRONT_BASE"

# senha sem eco
read -r -s -p "Senha ($LOGIN_EMAIL): " PASS; echo

TOKEN="$(
  curl -sS --max-time 6 "$API_BASE/api/v1/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"$LOGIN_EMAIL\",\"password\":\"$PASS\"}" \
  | jq -r '.access_token'
)"

[[ -n "$TOKEN" && "$TOKEN" != "null" ]] || die "Falhou pegar token (credenciais/rota)."

URL="$FRONT_BASE/#at=$TOKEN"

say "✅ URL (cole no celular):"
say "$URL"

# tenta copiar pro clipboard (se tiver)
if command -v xclip >/dev/null 2>&1; then
  printf "%s" "$URL" | xclip -selection clipboard
  say "📋 Copiado pro clipboard (xclip)."
elif command -v wl-copy >/dev/null 2>&1; then
  printf "%s" "$URL" | wl-copy
  say "📋 Copiado pro clipboard (wl-copy)."
fi

# abre no PC
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
  say "🧭 Abrindo no navegador (seu PC)."
else
  say "ℹ️ Sem xdg-open; copie a URL acima no navegador."
fi
