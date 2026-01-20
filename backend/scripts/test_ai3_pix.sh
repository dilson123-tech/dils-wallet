#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:8000"
EMAIL="user@example.com"

echo "== Saldo hoje =="
curl -s -X POST "$BASE/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: $EMAIL" \
  -d '{"message":"meu saldo hoje"}'
echo -e "\n\n"

echo "== Entradas do mês =="
curl -s -X POST "$BASE/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: $EMAIL" \
  -d '{"message":"quais foram minhas entradas do mês no pix?"}'
echo -e "\n\n"

echo "== Histórico do mês =="
curl -s -X POST "$BASE/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: $EMAIL" \
  -d '{"message":"me mostra o histórico do mês no pix"}'
echo -e "\n\n"

echo "== Resumo do mês (consultor) =="
curl -s -X POST "$BASE/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Email: $EMAIL" \
  -d '{"message":"faz um resumo do mês no pix"}'
echo -e "\n"
