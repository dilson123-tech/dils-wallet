#!/bin/bash
set -e

inicio=$(date +%s)
msg="${1:-deploy full backend+cliente}"

echo -e "\033[1;35m════════════════════════════════════════════\033[0m"
echo -e "\033[1;33m🚀 Deploy FULL: Backend + Cliente\033[0m"
echo -e "\033[1;37mMensagem: '$msg'\033[0m"
echo -e "\033[1;35m════════════════════════════════════════════\033[0m"

( cd backend && ./deploy.sh "$msg (backend)" )
( cd aurea-gold-client && ./deploy.sh "$msg (cliente)" )

fim=$(date +%s)
duracao=$((fim - inicio))
min=$((duracao / 60)); seg=$((duracao % 60))

echo -e "\033[1;35m════════════════════════════════════════════\033[0m"
echo -e "\033[1;32m✅ Deploy FULL concluído!\033[0m"
echo -e "\033[1;37m⏱️ Tempo total: ${min}m ${seg}s\033[0m"
echo -e "\033[1;35m════════════════════════════════════════════\033[0m"
