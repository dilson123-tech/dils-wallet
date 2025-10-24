#!/bin/bash
set -e

msg="${1:-deploy rápido}"
echo -e "\033[1;33m🚀 Iniciando deploy: $msg\033[0m"

git add -A
git commit -m "$msg" || echo "Nenhuma mudança para commitar"
git push origin main

echo -e "\033[1;36m📦 Subindo para Railway...\033[0m"
railway up --service dils-wallet2

echo -e "\033[1;32m✅ Deploy concluído com sucesso!\033[0m"
