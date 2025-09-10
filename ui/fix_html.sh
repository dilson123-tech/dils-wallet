#!/bin/bash
set -e

FILE="index.html"
BACKUP="index.html.bak.$(date +%Y-%m-%d-%H%M%S)"

if [[ "$1" == "restore" ]]; then
  LAST=$(ls -1t index.html.bak.* 2>/dev/null | head -n1)
  if [[ -z "$LAST" ]]; then
    echo "❌ Nenhum backup encontrado."
    exit 1
  fi
  cp -a "$LAST" "$FILE"
  echo "🔄 Restaurado do backup: $LAST → $FILE"
  exit 0
fi

# cria backup antes de mexer
cp -a "$FILE" "$BACKUP"
echo "📦 Backup criado: $BACKUP"

# 1) força charset
grep -q 'charset="utf-8"' "$FILE" || \
sed -i '0,/<head>/s//<head>\n  <meta charset="utf-8">/' "$FILE"

# 2) garante saldo
sed -i -E 's#<div id="saldo">.*</div>#<div id="saldo" style="font-size:30px; font-weight:800">--</div>#' "$FILE"

# 3) remove pagers duplicados
sed -i -E '/id="tx-pager"/,/<\/div>/d' "$FILE"

# 4) injeta pager único logo após </table>
sed -i '0,/<\/table>/{s//<\/table>\n  <div id="tx-pager" class="row" style="justify-content:center; gap:12px; margin-top:10px"><button id="tx-prev">Anterior<\/button><span id="tx-info" class="muted">Página 1<\/span><button id="tx-next">Próximo<\/button><\/div>/}' "$FILE"

# 5) ordem dos scripts
sed -i -E '/boot_api_base\.js|app\.js/d' "$FILE"
sed -i -E 's#</body>#  <script src="boot_api_base.js"></script>\n  <script src="app.js"></script>\n</body>#' "$FILE"

echo "✅ Correções aplicadas em $FILE"
