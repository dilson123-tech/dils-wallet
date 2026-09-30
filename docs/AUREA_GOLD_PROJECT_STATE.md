# Aurea Gold / Dils Wallet — Estado Oficial do Projeto (Handoff)

> Documento de handoff entre sessões. Somente fatos verificados no código.
> Referência de verificação: `origin/main` = `d05db94` (Merge pull request #292), auditado em 2026-09-28.
> Qualquer sessão futura deve revalidar estes fatos contra o `origin/main` vigente antes de agir.

---

## 1. IDENTIDADE DO PRODUTO

- **Nome do produto:** Aurea Gold (carteira digital com PIX e assistente de IA).
- **Nome do repositório/projeto técnico:** Dils Wallet (`dils-wallet`).
- **Natureza atual:** carteira em modo demonstração/sandbox. Não movimenta dinheiro real.
- **Modos de operação** (`WALLET_MODE`): `demo` (padrão) e `partner` (sandbox Asaas). Produção Asaas (`api.asaas.com`) é bloqueada por código e exige `REAL_MONEY_ENABLED=false`.

## 2. FONTE DE VERDADE

- **Repositório oficial local:** `/home/dilsondev/dils-wallet` (`~/dils-wallet`).
- **Remote oficial:** `https://github.com/dilson123-tech/dils-wallet.git`.
- **Referência do produto:** `origin/main`. Nenhuma outra branch, cópia, `/tmp` ou scratchpad é fonte de verdade.
- **Histórico, não referência:** PR #97 / `feat/wallet-shell-v2` (ver seção 12).
- **Documentos em `docs/` que divergem das evidências** (não usar como verdade sem revalidar):
  - `docs/product-maturity.md` descreve o produto como "production-grade" e "Market Readiness Medium-High". Isso não corresponde ao estado comprovado: sem dinheiro real, sem cash-in e sem PSP em produção.

## 3. ARQUITETURA ATUAL

| Camada | Tecnologia | Local |
|---|---|---|
| Backend | FastAPI (versão da app 0.3.0), SQLAlchemy | `backend/app` |
| Banco | Postgres (Railway); fallback SQLite | `backend/app/database.py` |
| Migrações | Alembic presente, mas o boot usa `Base.metadata.create_all` | `backend/` |
| Frontend | React + Vite + Tailwind | `aurea-gold-client/` |
| Deploy backend | Railway, com `backend/start.sh` (uvicorn) | — |
| IA | Cliente OpenAI (`OPENAI_API_KEY`, `OPENAI_MODEL`, padrão `gpt-4o-mini`) | `backend/app/api/v1/routes/ai.py`, `backend/app/api/v1/routes/ai_chat.py` |
| PSP/BaaS | Adapter Asaas, somente sandbox | `backend/app/partner/asaas_client.py`, `backend/app/partner/asaas_config.py`, `backend/app/partner/asaas_payment_correlation.py`, `backend/app/services/asaas_correlated_pix_payment_service.py` e `backend/app/api/v1/routes/wallet.py` |

- Resolução da API no frontend: `aurea-gold-client/src/lib/apiBase.ts` usa `VITE_API_BASE`, depois `http://<host>:8090`, depois `http://127.0.0.1:8090`.
- Autenticação: JWT HS256 fail-closed (exige `SECRET_KEY`/`JWT_SECRET`), access token de 30 min (expiração oficial, fixa em `backend/app/utils/security.py`; não existe variável de ambiente para alterá-la) e refresh token opaco (hash sha256, rotação com CAS).

## 4. FUNCIONALIDADES EXISTENTES

### Conta / Home
- Shell com abas: `aurea-gold-client/src/AppShell.tsx:19-23,34`, com **Conta** (home), **Gestão**, **Pagamentos** e **Mais**.
- `aurea-gold-client/src/super2/SuperAureaHome.tsx`: saldo, atalhos Receber/Extrato (~835/845, 1294-1295) e camadas **Cofrinhos**, **Investimentos** e **Cripto** (~665/675/685, 906-908).
- Insight PIX na Home consome `/ai/headline` (texto LAB, ver pendências).

### PIX
- Backend `backend/app/api/v1/routes/pix.py`:
  - `GET /pix/balance`: saldo do ledger (créditos − débitos).
  - `GET /pix/history`: histórico do `PixLedger` (`credit` → `entrada`, `debit` → `saida`), com `criado_em`.
  - Envio de PIX com idempotência, intent/ack e proteção de concorrência (`backend/app/services/pix_service.py`).
  - Forecast PIX com erro sanitizado.
- Frontend `aurea-gold-client/src/super2/AureaPixPanel.tsx`: Enviar PIX, Receber (UI) e Extrato (tile ~978).
- **Receber PIX:** existe na UI (`aurea-gold-client/src/super2/SuperAureaHome.tsx`, `aurea-gold-client/src/gestao/AureaGestaoPanel.tsx`, `aurea-gold-client/src/mais/AureaMaisPanel.tsx`). **Não há rota de cash-in ou cobrança no backend.**

### Gestão
- `aurea-gold-client/src/gestao/AureaGestaoPanel.tsx` (inclui atalho "Receber").

### Pagamentos
- `aurea-gold-client/src/pagamentos/AureaPagamentosPanel.tsx`, renderizado pela aba Pagamentos.
- `aurea-gold-client/src/pagamentos/PanelPagamentos.tsx` e `aurea-gold-client/src/pagamentos/PanelReservasIA3Lab.tsx` existem, mas **não são importados por nenhum arquivo** em `origin/main` (ver pendências).

### Mais
- `aurea-gold-client/src/mais/AureaMaisPanel.tsx` (inclui "Receber PIX").

### IA
- `POST /ai/chat`: exige `require_customer`. Usa saldo e histórico reais do ledger in-process, sem chamada HTTP interna, com rate limit.
- `/ai/summary` e insights PIX com auth (testes de caracterização).
- `/ai/headline` e `/headline-lab`: **sem auth**, com números fixos de LAB.
- `/ai/pagamentos_lab`: sem auth, só texto.

### Segurança
- JWT fail-closed; `whoami` canônico; `require_admin`/`require_customer`.
- Refresh com rotação CAS e testes de concorrência (SQLite e Postgres).
- Rate limit em login (por IP do cliente), refresh, IA e endpoints de parceiro/sandbox.
- Router `dev_seed` protegido por gate.
- Sanitização de erros no forecast PIX e nos adapters de wallet.
- CodeQL e pip-audit no CI.

### Infraestrutura
- Health/readiness (`/healthz` com `X-Health-Token`), Sentry opcional e workflows de smoke (ver seção 8).

### PSP / BaaS
- Adapter Asaas somente sandbox, com guardas de configuração (`backend/tests/test_asaas_config_guards.py`).
- Receptor de webhook Asaas (`backend/tests/test_asaas_webhook_receiver.py`).
- Rotas em `backend/app/api/v1/routes/wallet.py`: account-status, structured-balance, structured-statement, receipt-reconciliation, operational-limits, onboarding-status, sandbox payment/webhook/reconciliação/histórico.
- Cap de 5000 no sandbox, namespace por usuário e rate limit.
- Documentação: `docs/asaas/`, `WALLET_PARTNER_READINESS_MATRIX_V1.md`, `WALLET_PSP_BAAS_QUESTIONNAIRE_V1.md`, `WALLET_SANDBOX_CYCLE_RUNBOOK.md`.

## 5. FUNCIONALIDADES PROTEGIDAS

### NÃO REMOVER SEM AUTORIZAÇÃO

Confirmadas no código em `origin/main`:

- [x] Conta/Home, Saldo, Cofrinhos, Investimentos, Cripto, Gestão
- [x] PIX, Enviar PIX, Receber PIX (UI), Extrato, Pagamentos, Mais
- [x] Autenticação, refresh token (rotação CAS)
- [x] Ledger PIX, histórico PIX, idempotência, intent/ack, concorrência
- [x] IA (`/ai/chat` autenticado, summary, insights, headline)
- [x] Status da conta e do parceiro (`/wallet/account-status`, `onboarding-status`, readiness)
- [x] PSP/BaaS (adapter Asaas sandbox), webhooks, reconciliação
- [x] Observabilidade (Sentry opcional, logs), CI/CD, smoke tests, readiness/health
- [~] Métricas: existem métricas na UI (percentuais estimados na Home). Não foi confirmado endpoint dedicado de métricas operacionais.

Regra: nenhum item desta lista pode desaparecer para "simplificar" a Home ou qualquer painel.

## 6. ESTADO DE PRODUÇÃO (somente fatos comprovados)

- O CI em `origin/main` (`d05db94`) está todo verde.
- Os workflows agendados **Smoke Prod** e **health-prod** passam.
- Não há dinheiro real: `REAL_MONEY_ENABLED=false` é exigido e `api.asaas.com` é bloqueado por código.
- O crédito no ledger só é criado via seed (`backend/app/utils/ledger_seed.py`, `/dev-seed/seed-ledger`). O único writer em produção de fluxo é o débito do PIX (`backend/app/services/pix_service.py` ~299).
- O envio de PIX **não chama PSP**: é contábil interno.
- Não foram verificados nesta auditoria: variáveis reais da Railway, dados de produção e configuração do Asaas. Por regra, não houve acesso.

## 7. PORTAS E AMBIENTE LOCAL

| Item | origin/main (`d05db94`) | Branch local (`647b5c9`, não enviado) |
|---|---|---|
| `aurea-gold-client/src/lib/apiBase.ts` | **8090** | 8090 |
| `aurea-gold-client/vite.config.js` (proxy target) | 8000 | **8090** |
| `aurea-gold-client/.env.example` | 8000 | **8090** |
| `aurea-gold-client/src/dev/force-local-api.js` | 8000 | **8090** |
| Backend `backend/start.sh` | `$PORT` → `$RAILWAY_TCP_PROXY_PORT` → 8080 | igual |

- **A porta oficial de dev da API local é 8090.** Não assumir que 8000 é a porta oficial.
- A consolidação completa da 8090 depende do merge do commit `647b5c9` (`chore(dev): align frontend local API port to 8090`).
- Rodar localmente: backend com `--port 8090`; frontend com `npm run dev` em `aurea-gold-client/`.
- `backend/tests/test_pagination_smoke.py` usa `BASE` padrão `http://127.0.0.1:8000` e pula se o servidor estiver fora.

## 8. CI/CD

Workflows em `.github/workflows/`: `aurea-gold-smoke`, `cd`, `ci`, `codeql`, `fail_fast`, `health`, `notify_canary`, `notify_on_failure`, `notify_reusable`, `pip-audit`, `pix-concurrency-postgres`, `slack_test`, `smoke`, `smoke_pix`, `smoke_pr`, `smoke_prod`.

Jobs do `ci.yml`:
- `backend-build`: `compileall`.
- `backend-tests`: `python -m pytest tests -q -rs -p no:cacheprovider`, com SECRET_KEY fictícia e SQLite. Os testes Postgres se pulam e são cobertos por `pix-concurrency-postgres.yml`.
- `client-build`: `npm ci` + `npm run build`.
- `smoke-prod`: só na `main`, com gate de secrets (`SMOKE_BASE_URL`, `HEALTH_TOKEN`).
- `lint` (gate): exige sucesso de `backend-build`, `client-build` e `backend-tests`.

Commit, push, PR e deploy só com autorização explícita do usuário, renovada a cada vez.

## 9. TESTES

- 40 arquivos em `backend/tests/`, cobrindo:
  - auth, whoami e authz;
  - refresh (concorrência e rate limit);
  - login rate limit;
  - PIX (ledger, histórico, balance 7d, envio, idempotência, intent, contrato HTTP, concorrência Postgres);
  - IA (chat, summary, rate limit, caracterização de auth);
  - Asaas (client, config guards, webhook);
  - wallet (sanitização, rate limit, sandbox end-to-end, cap, correlação de pagamento);
  - Sentry, startup, `dev_seed` gate e remoção do admin dbfix.
- Smoke em shell: `scripts/smoke_prod.sh`, que valida o contrato de `/pix/history` sem imprimir valores.
- Fora do CI na prática: `backend/tests/test_pagination_smoke.py`, que depende de um servidor rodando e pula sem ele.

## 10. PENDÊNCIAS COMPROVADAS

Legenda: 🔴 bloqueador para dinheiro real · 🟠 importante · 🟡 hardening/limpeza. A coluna "Tipo" diz se a pendência exige **mudança** ou só **acompanhamento**.

| # | Prio | Problema | Arquivo/rota | Impacto | Tipo |
|---|---|---|---|---|---|
| 1 | 🔴 | Sem logout nem revogação de tokens | auth/refresh | Sessão comprometida não pode ser encerrada | Mudança |
| 2 | 🔴 | Sem cash-in: crédito só via seed | `backend/app/utils/ledger_seed.py`, `/dev-seed/seed-ledger` | Receber PIX é só UI | Mudança (depende de PSP) |
| 3 | 🔴 | Envio PIX não chama PSP | `backend/app/services/pix_service.py` ~299 | PIX é contábil interno | Mudança (depende de PSP) |
| 4 | 🔴 | Dependência de parceiro PSP/BaaS e de requisitos regulatórios | — | Impede operação real | Acompanhamento |
| 5 | 🟠 | `/pix/balance` e `/pix/history` escondem exceção com 200 (saldo 0 `"source": "lab"` e `[]`) | `backend/app/api/v1/routes/pix.py` (~102-106, ~152) | Falha de banco parece conta vazia | Mudança |
| 6 | 🟠 | Métricas percentuais fixas em modo real (×0.22, ×0.18, ×0.32, ×0.4, ×0.12, ×0.08, /1550) | `aurea-gold-client/src/super2/SuperAureaHome.tsx` ~705-728 | Números apresentados como reais | Mudança: rotular como estimativa, **não remover** |
| 7 | 🟠 | Passo "Auth sanity" chama rota inexistente `/api/v1/transactions/balance` | `.github/workflows/ci.yml:147-157` | Falharia se `BEARER_TOKEN` fosse configurado | Mudança |
| 8 | 🟡 | Headline/Insight PIX usa texto e números fixos de LAB, sem auth | `/ai/headline`, `/headline-lab`; `aurea-gold-client/src/super2/SuperAureaHome.tsx:408`, `aurea-gold-client/src/super2/AureaIAPanel.tsx:106`, `aurea-gold-client/src/credito/AureaCreditoIAPanel.tsx:147`, `aurea-gold-client/src/super2/IaHeadlineLab.tsx:34` | UI mostra "Headline LAB funcionando" | Mudança |
| 9 | 🟡 | Refresh de 30 vs 7 dias; JWT de refresh sem revogação; fallback ultra-legacy | auth | Superfície de sessão maior | Mudança |
| 10 | 🟡 | Claim `typ` não checado no authz | auth | Tipo de token não validado | Mudança |
| 11 | 🟡 | ~~`ACCESS_TOKEN_EXPIRE_MINUTES=60` não é usado (efetivo: 30)~~ — resolvido: config morta removida de `backend/app/config.py`; expiração oficial do access token é 30 min, fixa em `backend/app/utils/security.py`, sem variável de ambiente | config | — | Resolvido |
| 12 | 🟡 | uvicorn em `--log-level debug` | `backend/start.sh:26` | Logs verbosos em produção | Mudança |
| 13 | 🟡 | `create_all` no boot em vez de Alembic | startup | Evolução de schema frágil | Mudança |
| 14 | 🟡 | `{exc}` exposto no `detail` dos 503 do sandbox | `backend/app/api/v1/routes/wallet.py:946, 1596, 1829, 2035` | Possível vazamento de detalhe interno | Mudança |
| 15 | 🟡 | `descricao` sem `max_length` | schemas PIX | Payload arbitrário | Mudança |
| 16 | 🟡 | Comparação com `!=` (não constante) no admin-reset-passwd | `backend/app/routers/dev_seed.py` ~165 | Timing (rota com gate) | Mudança |
| 17 | 🟡 | `Transaction.valor` em float | models | Precisão monetária | Mudança |
| 18 | 🟡 | Exceções aceitas no pip-audit (CVE-2024-23342, PYSEC-2025-183) | `.github/workflows/pip-audit.yml` | Risco aceito | Acompanhamento |
| 19 | 🟡 | `test_pagination_smoke.py` fora do CI na prática | `backend/tests/test_pagination_smoke.py` | Sem cobertura efetiva | Acompanhamento |
| 20 | 🟡 | `PanelPagamentos.tsx`/`PanelReservasIA3Lab.tsx` não importados; chamam `/api/v1/reservas/painel` e `/ai/reservas_insights_lab`, inexistentes | `aurea-gold-client/src/pagamentos/` | Código morto | Acompanhamento (não remover sem autorização) |
| 21 | 🟡 | Porta 8090 só consolidada após o merge de `647b5c9` | ver seção 7 | Proxy/dev apontando para 8000 no origin/main | Mudança (commit já existe localmente) |
| 22 | 🟡 | `docs/product-maturity.md` superestima a maturidade | docs | Expectativa incorreta | Mudança (doc) |

**Legado presente, não alterado:** `backend/app/api/v1/routes/pix.py.fullbak`, `backend/app/api/v1/routes/pix.py.fullbak.1759859805`, `backend/app/api/v1/routes/pix_daily.py`, `backend/app/api/v1/routes/agents.py` e `backend/app/api/v1/routes/health.py` não montados, `backend/app/schemas/_legacy_schemas_backup.py`, `backend/app/models/user_legacy_backup_do_nao_usar.disabled.py`, `backend/app/db_force_refresh_rebuild.py`, `backend/app/db_rebuild_refresh.py`, `backend/app/static/`, `backend/app/templates/`.

## 11. ITENS FORA DO ESCOPO (até autorização explícita)

- Operar dinheiro real ou habilitar `api.asaas.com`.
- Alterar Railway, Asaas ou variáveis de produção.
- Chamadas externas pagas ou com chaves reais.
- Remover, substituir ou simplificar funcionalidades existentes (seção 5).
- Remover código legado (seção 10) sem análise e autorização.
- Merge do PR #97.

## 12. PRs/BRANCHES HISTÓRICOS

- **PR #97 / `feat/wallet-shell-v2`:** histórico. **Não é referência** e **não deve ser mergeado**. Comparações usam `git show`/`git diff` contra refs, sem cópias extraídas.
- **`fix/pix-history-ledger-pr`:** contém `647b5c9` (porta 8090), 1 commit à frente do remoto no momento desta auditoria. Não enviado.

## 13. PROTOCOLO PARA FUTURAS SESSÕES

- [ ] `pwd`
- [ ] `git rev-parse --show-toplevel` e confirmar que é `/home/dilsondev/dils-wallet`
- [ ] `git branch --show-current` e confirmar que é a branch pedida pelo usuário
- [ ] `git status --short --branch`
- [ ] `git remote -v` e confirmar `dilson123-tech/dils-wallet`
- [ ] `git fetch origin`
- [ ] `git log -1 --oneline --decorate origin/main`
- [ ] Ler este documento (`docs/AUREA_GOLD_PROJECT_STATE.md`) e revalidá-lo contra o `origin/main` atual
- [ ] Identificar o escopo exato da tarefa
- [ ] Não alterar nada fora do escopo
- [ ] Testar (`pytest` do backend e build do client, conforme o caso)
- [ ] Revisar o diff (`git diff --check`, `git diff`)
- [ ] Só então pedir autorização para commit, push, PR ou deploy (cada um separadamente)
- [ ] Nunca imprimir tokens, senhas, segredos ou valores de itens financeiros em logs

## 14. REGRA DE SEGURANÇA

**Nenhuma funcionalidade existente será removida, substituída ou simplificada sem evidência técnica, comparação com origin/main e autorização explícita.**

Princípios:
- Se existe e funciona, preservar.
- Se existe mas tem problema comprovado, documentar.
- Se não existe, não inventar.
- Se não há evidência de problema, não alterar.

---

## 15. ESTIMATIVA DE MATURIDADE

Sem percentuais: não há métrica objetiva que sustente um número. Os três eixos são independentes e não devem ser combinados.

### A. Maturidade do software
Alta para um produto em modo demo/sandbox. O CI está verde, a suíte de 40 arquivos cobre auth, refresh, ledger PIX, idempotência, intent/ack e concorrência (inclusive Postgres), IA autenticada e adapter Asaas sandbox, e os smoke tests de produção passam.

### B. Hardening pendente
Moderado. Ver itens 🟠 e 🟡 da seção 10: erros mascarados com 200 no PIX, métricas fixas na UI, headline LAB, logout e revogação, log em debug, `create_all`, float monetário, detalhe de exceção nos 503 do sandbox e passo quebrado no CI.

### C. Prontidão para operação financeira real
Não pronto. Faltam cash-in, integração do envio PIX com PSP, parceiro PSP/BaaS contratado e produção habilitada, requisitos regulatórios, e logout/revogação (itens 🔴 da seção 10). O dinheiro real está bloqueado por código, intencionalmente.
