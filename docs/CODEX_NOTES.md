# Dils Wallet — Guia rápido do Codex

Use este resumo para colaborar com o Codex neste monorepo (FastAPI + UIs estáticas/React). Não altere `requirements*.txt` ou outros arquivos de dependências sem pedir.

## Modos de aprovação / sandbox
- Sandbox: por padrão `workspace-write` (edita só o repo) e rede `restricted`.
- Aprovação: tipicamente `on-request`. Se um comando falhar por sandbox ou precisar de rede/escalada, o Codex vai reenviar com `with_escalated_permissions=true` e uma justificativa curta.
- Não pedir aprovação para ações destrutivas (ex.: `git reset --hard`) a menos que o usuário peça explicitamente.
- Se o sandbox estiver `read-only`, qualquer comando de escrita precisa de aprovação.

## Como pedir tarefas ao Codex
- Seja direto: o que mudar, onde, e qual o resultado esperado. Ex.: “Adicionar rota PIX X em `backend/app/api/v1/routes/...` e expor no `main.py`”.
- Para comandos, peça explicitamente: ex.: “rode os testes `./backend/smoke.sh`”.
- Lembre o contexto de rede: instalações externas podem exigir aprovação ou serem bloqueadas.

## Revisar mudanças com `/review`
- Depois de o Codex propor/aplicar um patch, peça “/review” para rodar a checagem automática de regressões. O CLI chamará o revisor interno e mostrará os achados (P0/P1...).
- Use para validar antes de aceitar: checa gaps como dependências removidas, erros de import, regressões óbvias etc.

## Aprovar com `/approve`
- Quando o resultado estiver ok, use “/approve” para sinalizar que as mudanças propostas estão aceitas.
- Antes disso, confirme que o patch não altera arquivos sensíveis (ex.: requirements) e que testes relevantes foram mencionados/rodados.

## Dicas rápidas (repositório)
- Backend: FastAPI em `backend/app/main.py` com rotas em `backend/app/api/v1/routes/`. Evite mexer em deps sem necessidade.
- Frontends: estáticos em `frontend/` e React em `aurea-gold-client/` e `aurea-gold-admin/`.
- Testes: scripts de smoke (`backend/smoke.sh`, `smoke.sh` na raiz) e healthchecks.
