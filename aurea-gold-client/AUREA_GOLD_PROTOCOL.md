# 🏦 AUREA GOLD – PROTOCOLO OFICIAL DE DESENVOLVIMENTO

## 🔒 REGRA 1 – CHECKPOINT OBRIGATÓRIO
Antes de qualquer alteração estrutural:
- git status
- git add .
- git commit -m "checkpoint antes de <alteração>"

Nunca editar JSX grande sem checkpoint.

---

## 🌿 REGRA 2 – ALTERAÇÕES EXPERIMENTAIS
Mudanças grandes devem ser feitas em branch própria:

git checkout -b exp/nome-da-feature

Se quebrar:
git checkout main
git branch -D exp/nome-da-feature

---

## 🧪 REGRA 3 – TESTE ANTES E DEPOIS
Antes de alterar:
npx tsc --noEmit

Depois de alterar:
npx tsc --noEmit

Se quebrar → restaurar imediatamente.

---

## 🧱 REGRA 4 – NUNCA USAR SED EM JSX GRANDE
Alterações estruturais devem ser:
- Pequenas
- Controladas
- Isoladas
- Preferencialmente via novo componente

---

## 📌 REGRA 5 – DEFINIÇÃO DE VERSÃO ESTÁVEL
Uma versão é considerada estável quando:

✔ Compila limpo
✔ UI funcional
✔ Regras financeiras coerentes
✔ Nenhum erro no console

Após isso, congelar versão.

---

## 🏁 STATUS ATUAL
Aurea Gold v1.0 Core Stable
- Saldo real funcionando
- Forecast funcionando
- Risco coerente com saldo
- Layout funcional
