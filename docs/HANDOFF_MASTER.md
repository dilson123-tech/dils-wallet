# HANDOFF MASTER — Aurea Gold / Dils Wallet

> Documento mestre de passagem de contexto entre sessões.
> Criado em 2026-10-28 na branch `docs/handoff-master` (base `origin/main` = `d85c919a`).
> Complementa, sem substituir, `docs/AUREA_GOLD_PROJECT_STATE.md`.

**Legenda de evidência**

| Marca | Significado |
|---|---|
| **[VERIFICADO @ d85c919a]** | Conferido diretamente no código/Git/GitHub em 2026-10-28 contra `origin/main` `d85c919a`. |
| **[HISTÓRICO]** | Relato de documento ou sessão anterior; não reconferido nesta data. |
| **[INCONCLUSIVO]** | Evidência insuficiente para afirmar o estado; requer investigação antes de agir. |

Este documento **não contém segredos**. É proibido registrar aqui valores de variáveis de ambiente, tokens, senhas, hashes de senha ou credenciais. Nomes de variáveis (ex.: `REAL_MONEY_ENABLED`) podem ser citados, sempre sem seus valores.

---

## 1. Identificação, objetivo e arquitetura

- **Produto:** Aurea Gold — carteira digital com PIX e assistente de IA. Repositório `dils-wallet`. [VERIFICADO @ d85c919a]
- **Modo de operação:** demo/sandbox. `WALLET_MODE` = `demo` (padrão) ou `partner` (Asaas sandbox). `api.asaas.com` (produção) bloqueado; exige `REAL_MONEY_ENABLED=false`. **Não há dinheiro real.** [HISTÓRICO — PROJECT_STATE §1; guards confirmados em sessão anterior]
- **Objetivo deste handoff:** permitir que qualquer sessão futura (humana ou agente) retome o projeto com o estado verificado, as regras de autorização e a lista reconciliada de pendências, sem re-derivar contexto nem alterar o que já funciona.

**Arquitetura** [HISTÓRICO — PROJECT_STATE §3, base `d05db94`; pastas confirmadas @ d85c919a]

| Camada | Tecnologia / local |
|---|---|
| Backend | FastAPI + SQLAlchemy em `backend/app` |
| Banco | Postgres (Railway), fallback SQLite (`database.py`); Alembic presente, boot via `create_all` |
| Cliente | React + Vite + Tailwind em `aurea-gold-client/` |
| Admin | React + Vite em `aurea-gold-admin/` (V1 em PR #315, não mergeado) |
| Deploy | Railway, `backend/start.sh` |
| IA | OpenAI `gpt-4o-mini` (`routes/ai.py`, `ai_chat.py`) |
| Parceiro | Asaas sandbox (`partner/asaas_client.py`, `asaas_config.py`, `asaas_payment_correlation.py`, `services/asaas_correlated_pix_payment_service.py`, `wallet.py`) |
| Auth | JWT HS256 fail-closed, access 30 min (`utils/security.py`), refresh opaco com sha256 + CAS |
| API base do cliente | `apiBase.ts`: `VITE_API_BASE` → `<host>:8090` → `127.0.0.1:8090` |

---

## 2. Repositório, branches e estado Git verificado

[VERIFICADO @ d85c919a, 2026-10-28]

| Item | Valor |
|---|---|
| Caminho oficial | `/home/dilsondev/dils-wallet` (único local autorizado) |
| Remoto | `https://github.com/dilson123-tech/dils-wallet.git` |
| `origin/main` | `d85c919a5f5bdae0fafd628d66d5a042b77f764a` — Merge PR #314 (2026-10-28 19:29 -0300) |
| `main` local | `bffc6dd2` — **13 commits atrás** de `origin/main` (não atualizado; não é necessário para trabalho em branches) |
| Branches locais | 61 (incluindo `docs/handoff-master`) — **nenhuma deve ser excluída** |
| Branch IaC | `chore/railway-iac-migration` = `7cf36a49` — **não alterar** |
| Branch admin V1 | `feat/admin-frontend-v1` = `74b72eb9` (PR #315) |
| Arquivo não rastreado | `.railway/railway.ts` — sha256 `3c729db23ad11e4525567dec52ac6a205b2237befa23439e978237d6cfa98eee` — **preservar; nunca commitar** |

**Stashes (preservar; não aplicar, não descartar)**

| Ref | Descrição |
|---|---|
| `stash@{0}` | On fix/refresh-reuse-identity-map: p0p1-protecao antes de ff feat para cb561ef6 |
| `stash@{1}` | On chore/provision-smoke-user: WIP smoke-prod antes de sincronizar main |
| `stash@{2}` | On fix/token-truncado: checkpoint(rescue): antes do rollback (token-truncado) |
| `stash@{3}` | On main: WIP: recover painel (antes de trocar p/ feature branch) |

**Merges recentes em `origin/main`** (PRs #291–#314, todos MERGED) [VERIFICADO @ d85c919a]

| Tema | PRs |
|---|---|
| Ledger / histórico PIX | #291, #292, #293, #294, #296 |
| Dependências | #295 (PyJWT), #311 (certifi), #312 (dnspython) |
| Auth / sessão | #297, #298, #299, #300, #301, #302, #303, #307 |
| Headline LAB com auth | #304 |
| PIX / Asaas | #305, #306, #308, #309, #310 |
| GIT_SHA no boot | #313 |
| Admin: listagem paginada de usuários | #314 |

---

## 3. Fontes de verdade e mapa da documentação

**Hierarquia de verdade**

1. Código em `origin/main` (sempre prevalece). [VERIFICADO]
2. Este documento (`docs/HANDOFF_MASTER.md`) — estado reconciliado em 2026-10-28.
3. `docs/AUREA_GOLD_PROJECT_STATE.md` — base `d05db94` / PR #292, auditado em 2026-09-28. Parcialmente desatualizado (ver §8). [HISTÓRICO]
4. Demais documentos — ver mapa abaixo; vários são genéricos ou obsoletos.

**Mapa da documentação** [VERIFICADO @ d85c919a]

| Documento | Situação |
|---|---|
| `docs/AUREA_GOLD_PROJECT_STATE.md` | Referência principal anterior; 22 pendências; protocolo de sessão |
| `SECURITY.md` | Genérico; afirma "production-oriented… not a demo repository" — **conflita** com modo demo/sandbox; sem canal de contato |
| `docs/architecture.md` | Tom comercial ("production-grade"); não reflete o estado real |
| `docs/deploy.md` | Genérico; não cita Railway, `start.sh`, IaC nem GIT_SHA |
| `backend/README.md` | MVP de 2025-09-03, **obsoleto** (porta 8686, `/ui`, rota inexistente, seção duplicada, credencial de exemplo — não reproduzir) |
| `docs/CODEX_NOTES.md` | **Conflito**: instrui não pedir aprovação para ações destrutivas (ex.: `git reset --hard`); cita `frontend/`, `backend/smoke.sh`, `/review`, `/approve` inexistentes. **Não seguir** — prevalece §4 |
| `docs/github-governance.md` | Ruleset `aurea-main-guard`; checks `lint` e `smoke` strict; 0 aprovações |
| `docs/product-maturity.md` | Divergente do estado real (pendência 22) |
| `docs/panels.md`, `docs/pix-operation.md`, `docs/WALLET_*` (5) | Referência funcional |
| `docs/asaas/` (7) | Integração Asaas sandbox |
| `docs/archive/asaas` (~50), `docs/archive/wallet` | Arquivo — "preservado, não atualizado" |
| `aurea-gold-client/docs/` (5) | Docs do cliente |
| `.handoff_backup`, `*.bak` na raiz | Backups de UI legados — não remover sem autorização |
| `AGENTS.md`, `CLAUDE.md`, `HANDOFF` | **Não existiam** antes da criação deste documento (2026-10-28). `AGENTS.md` e `CLAUDE.md` continuam inexistentes; o handoff mestre agora é este arquivo, `docs/HANDOFF_MASTER.md` |

---

## 4. Regras de segurança, autorização e preservação

**Regra-mestra** (PROJECT_STATE §14, literal):

> **Nenhuma funcionalidade existente será removida, substituída ou simplificada sem evidência técnica, comparação com origin/main e autorização explícita.**

- Se existe e funciona, preservar.
- Se existe mas tem problema comprovado, documentar.
- Se não existe, não inventar.
- Se não há evidência de problema, não alterar.

**Autorização**

- Commit, push, PR, merge e deploy exigem **cada um** autorização explícita e separada do responsável. Aprovação de uma etapa não se estende à seguinte.
- Antes de qualquer mudança: preflight Git (§12) e prova do problema.
- Após qualquer mudança, reportar: arquivos; o que mudou e por quê; testes e resultados; o que **não** mudou; se houve commit/push/deploy.
- Havendo bloqueio: **parar e informar**. Não contornar proteções de branch nem forçar operações.

**Proibições permanentes**

- Não modificar Railway, variáveis, segredos, banco, PIX, saldo, ledger ou Asaas sem autorização específica.
- Não executar manualmente deploy, redeploy, restart, rollback, cutover ou alterações de infraestrutura.
- Não alterar `chore/railway-iac-migration` nem incluir `.railway/railway.ts` em commits.
- Não excluir branches, stashes ou arquivos locais; não descartar alterações locais.
- Não usar `git add -A`; adicionar arquivos por caminho explícito.
- Não declarar produção atualizada sem evidência do deploy concluído **e** do SHA correspondente.
- Não ler, exibir ou registrar credenciais (`.env*`, bancos SQLite locais, configuração do Railway CLI, arquivos de senha de teste).
- Dinheiro real / `api.asaas.com`: fora de escopo.

**Itens protegidos — "NÃO REMOVER SEM AUTORIZAÇÃO"** [HISTÓRICO — PROJECT_STATE §5]

Conta/Home, Saldo, Cofrinhos, Investimentos, Cripto, Gestão, PIX (Enviar, Receber UI, Extrato), Pagamentos, Mais, Auth e refresh CAS, Ledger/histórico/idempotência/intent-ack/concorrência, IA, status de conta e parceiro, PSP/BaaS/webhooks/reconciliação, observabilidade, CI/CD, smoke, health, métricas (parcial). Nada desaparece para "simplificar".

---

## 5. Funcionalidades comprovadas e evidências

| Funcionalidade | Evidência | Marca |
|---|---|---|
| Logout server-side (`/logout`, `/logout-all`) | `auth.py:350`, `auth.py:368`; PRs #301/#303/#307 | [VERIFICADO @ d85c919a] |
| Refresh opaco com detecção de reuso | PRs #299, #300, #302, #303, #307 | [VERIFICADO @ d85c919a — merges] |
| Expiração do access token sem config morta | PR #298 | [VERIFICADO @ d85c919a — merge] |
| IA `/ai/chat` exige cliente + rate limit 30/min | `ai_chat.py:752-757`, `require_customer`; PR #304 | [VERIFICADO @ d85c919a] |
| PIX envio fail-closed sem PSP | PR #305 | [VERIFICADO @ d85c919a — merge] |
| Erros PIX genéricos (503) | `pix.py:102-106`, `151-155`, `197-201` | [VERIFICADO @ d85c919a] |
| Erros 503 genéricos em wallet | `wallet.py` 966, 1142, 1741, 1800, 2033, 2239, 2501 | [VERIFICADO @ d85c919a] |
| Crédito Asaas sandbox idempotente (PAYMENT_RECEIVED) | `wallet.py:407`, `:1132`, `:1277`, `:2477`; `config.py:45`; PRs #306/#308 | [VERIFICADO @ d85c919a] |
| Resposta PIX idempotente com `valor` decimal | PR #310 | [VERIFICADO @ d85c919a — merge] |
| GIT_SHA a partir do commit Railway | PR #313 | [VERIFICADO @ d85c919a — merge] |
| Listagem paginada de usuários admin (backend) | PR #314 | [VERIFICADO @ d85c919a — merge] |
| Limite de tamanho em `pix_send` | `schemas/pix_send.py:8`, `:23` (`max_length=255`) | [VERIFICADO @ d85c919a] |
| Shell do cliente (Conta, Gestão, Pagamentos, Mais) e painéis | `AppShell.tsx`, `Aurea*Panel.tsx` | [HISTÓRICO — PROJECT_STATE §4] |
| `/healthz` com `X-Health-Token`, Sentry opcional | PROJECT_STATE §4 | [HISTÓRICO] |
| Smoke Prod e health-prod passando | PROJECT_STATE §6 (base `d05db94`) | [HISTÓRICO] |

---

## 6. Decisões técnicas e histórico relevante

- **PR #97 / `feat/wallet-shell-v2`:** histórico; **não deve ser mergeado**. [HISTÓRICO]
- **`647b5c9`** (`fix/pix-history-ledger-pr`): está em `origin/main`. [VERIFICADO @ d85c919a]
- **Porta oficial de dev = 8090** (`vite.config.js:9`, `.env.example:1`, `force-local-api.js:9`, `apiBase.ts:14,19`). `start.sh` usa `$PORT` → `$RAILWAY_TCP_PROXY_PORT` → 8080. [VERIFICADO @ d85c919a]
- **Ledger como fonte do saldo/histórico** (PRs #291–#294, #296). [VERIFICADO — merges]
- **Fail-closed por padrão** em JWT e envio PIX sem PSP. [VERIFICADO — merges]
- **Crédito em produção apenas via seed** (`ledger_seed.py`, `/dev-seed/seed-ledger`) em base `d05db94`. [HISTÓRICO]
- **Maturidade em 3 eixos, sem percentuais:** software alto para demo; hardening moderado; operação real **não pronta**. [HISTÓRICO — PROJECT_STATE §15]

---

## 7. Auditorias e testes

| Item | Estado | Marca |
|---|---|---|
| Arquivos `test_*` em `backend/tests` | **58** (PROJECT_STATE diz 40 — desatualizado) | [VERIFICADO @ d85c919a] |
| Workflows em `.github/workflows` | 16: aurea-gold-smoke, cd, ci, codeql, fail_fast, health, notify_canary, notify_on_failure, notify_reusable, pip-audit, pix-concurrency-postgres, slack_test, smoke, smoke_pix, smoke_pr, smoke_prod | [VERIFICADO @ d85c919a] |
| Jobs de `ci.yml` | backend-build, backend-tests, client-build, smoke-prod, lint (gate) | [HISTÓRICO] |
| Smoke de produção | `scripts/smoke_prod.sh` | [HISTÓRICO] |
| Ruleset de `main` | `aurea-main-guard`: `lint` + `smoke` strict, 0 aprovações | [HISTÓRICO — github-governance.md] |
| Auditoria de dependências | `pip-audit.yml:30` ignora CVE-2024-23342 e PYSEC-2025-183 | [VERIFICADO @ d85c919a] |
| Revalidação das 22 pendências | Concluída em 2026-10-28 (§8) | [VERIFICADO @ d85c919a] |
| Variáveis do Railway | Não verificadas (fora de escopo; somente leitura) | [INCONCLUSIVO] |

---

## 8. As 22 pendências reconciliadas

Revalidadas contra `origin/main` `d85c919a` em 2026-10-28.

| # | Tema | Estado | Evidência |
|---|---|---|---|
| 1 | Logout server-side | **RESOLVIDO** | #301/#303/#307; `auth.py:350`, `:368` |
| 2 | Cash-in real | **PARCIAL** | Sandbox Asaas com crédito idempotente (`wallet.py:407`, `:1132`, `:1277`, `:2477`; `config.py:45`); sem cash-in real |
| 3 | Payout real | **PARCIAL / mitigado** | #305 fail-closed; sem payout real |
| 4 | Parceiro PSP / regulatório | **ABERTO (acompanhamento)** | Dependência externa |
| 5 | Vazamento de detalhe de erro em PIX | **RESOLVIDO** | `pix.py:102-106`, `151-155`, `197-201` → 503 genérico |
| 6 | Valores derivados fixos na Home | **ABERTO** | `SuperAureaHome.tsx:707` ×0.22, `:711` ×0.18, `:714` ×0.32, `:727` /1550, sob `!isDemoWallet` |
| 7 | CI chama rota inexistente | **ABERTO** | `ci.yml:147-157` → `/api/v1/transactions/balance` (inexistente; único `/balance` em `pix.py:68`); só roda com `BEARER_TOKEN` |
| 8 | IA headline LAB | **PARCIAL** | Auth resolvida (#304); números LAB fixos permanecem |
| 9 | Refresh legado | **RESOLVIDO** | #299/#300 |
| 10 | Validação do tipo de token | **PARCIAL** | `utils/authz.py:27-29` rejeita `typ=="refresh"`; falta validação positiva |
| 11 | Config morta de expiração | **RESOLVIDO** | #298 |
| 12 | Log verboso em produção | **ABERTO** | `backend/start.sh:29` `--log-level debug --access-log` |
| 13 | Caminho de inicialização do banco | **INCONCLUSIVO** | `utils/init_db.py:23`, `utils/db_wait.py:25`, `entrypoint.py:44` `_boot_init_db()`; `start.sh` sobe `app.main:app`; existe `backend/app/main.py.broken.1762218406` |
| 14 | `str(exc)` em respostas | **RESOLVIDO / residual baixo** | 503 genéricos; restam `str(exc)` em 422 (`wallet.py:2531`, `:2688`) |
| 15 | Limites de tamanho em schemas | **RESOLVIDO / PARCIAL** | `pix_send.py` ok; demais schemas não auditados |
| 16 | Comparação de segredo em tempo constante | **PARCIAL** | `dev_seed.py:32` usa `compare_digest`; `:179` ainda usa `!=` |
| 17 | Valores monetários em float | **ABERTO** | `models/transaction.py:15` `DOUBLE_PRECISION` (`reservas.py:36` é Numeric; #310 só converte a resposta) |
| 18 | CVEs ignoradas no pip-audit | **ABERTO (acompanhamento)** | `pip-audit.yml:30` |
| 19 | Teste com BASE fixa | **ABERTO** | `test_pagination_smoke` usa `127.0.0.1:8000` |
| 20 | Painéis órfãos | **ABERTO** | ex.: `PanelPagamentos.tsx:2` importa `PanelReservasIA3Lab` |
| 21 | Porta de dev divergente | **RESOLVIDO / residual** | 8090 oficial; ainda divergem `test_pagination` (8000), `backend/README` (8686/8000), `start.sh` (`$PORT`) |
| 22 | `product-maturity.md` divergente | **ABERTO** | Arquivo existe |

**Resumo:** 6 resolvidos (1, 5, 9, 11, 14, 21 — os dois últimos com residual), 6 parciais (2, 3, 8, 10, 15, 16), 9 abertos (4, 6, 7, 12, 17, 18, 19, 20, 22), 1 inconclusivo (13).

**Legado conhecido (não remover sem autorização)** [HISTÓRICO — PROJECT_STATE §10]: `pix.py.fullbak*`, `pix_daily.py`, `agents.py` e `health.py` não montados, `_legacy_schemas_backup.py`, `user_legacy_backup_do_nao_usar.disabled.py`, `db_force_refresh_rebuild.py`, `db_rebuild_refresh.py`, `static/`, `templates/`, `main.py.broken.1762218406`.

---

## 9. Riscos, conflitos documentais e bloqueios

**Conflitos documentais**

- `docs/CODEX_NOTES.md` autoriza ações destrutivas sem aprovação → **contradiz §4**. Prevalece §4. [VERIFICADO]
- `SECURITY.md` e `docs/architecture.md` descrevem o projeto como produção → **contradiz o modo demo/sandbox**. [VERIFICADO]
- `backend/README.md` e `docs/deploy.md` obsoletos/genéricos. [VERIFICADO]
- PROJECT_STATE: contagem de testes (40 vs 58) e status de várias pendências desatualizados. [VERIFICADO]

**Riscos técnicos**

- Valores monetários em float (pendência 17).
- Log `debug` + access log em produção (pendência 12).
- Caminho de init de banco incerto (pendência 13).
- Passo do CI apontando para rota inexistente (pendência 7) — falso positivo/negativo silencioso quando `BEARER_TOKEN` existir.

**Bloqueios**

- **IaC Railway:** bloqueada até resposta do Railway (prazo 2026-12-01). Tópico público: https://station.railway.com/questions/config-as-code-iac-migration-railway-bab3852f. Rascunho de consulta de suporte é **privado e não deve ser publicado**. [HISTÓRICO]
- **Operação real:** depende de PSP/regulatório (pendência 4).

---

## 10. Estado do PR #315 e da migração Railway IaC

**PR #315 — `feat(admin): integrate real authentication and users list`** [VERIFICADO em 2026-10-28 via GitHub]

| Item | Valor |
|---|---|
| Branch / HEAD | `feat/admin-frontend-v1` / `74b72eb96aac0f3dfcbc3c6c717444bb0d016d8a` |
| Estado | OPEN, MERGEABLE, `mergeStateStatus` CLEAN, checks verdes |
| Checks | 13 SUCCESS, 2 SKIPPED (verificado em 2026-10-28 via `gh pr view 315`) |
| Merge / deploy | **NÃO autorizados** |

Pendências para deploy do admin [HISTÓRICO — sessão de 2026-10-28]:

- Hospedagem do admin e `VITE_API_BASE`.
- `CORS_ORIGINS` no backend incluindo a origem do admin.
- Build de produção quebrado: TS1127/TS1160 em `src/api/users.ts`, TS7016 em `vite.config.ts`, ausência de `eslint.config`.
- Fallback SPA no host.
- Conta admin em produção.

Achados não bloqueantes: refresh permanece válido se o logout falhar; 401 em `whoami` após login OK; tokens em `localStorage`; arquivos legados no admin.

**Migração Railway IaC** [HISTÓRICO]

- Branch `chore/railway-iac-migration` = `7cf36a49`; arquivo local não rastreado `.railway/railway.ts` (sha256 em §2).
- Bloqueada aguardando Railway (prazo 2026-12-01). Não alterar a branch nem commitar o arquivo.

---

## 11. Próxima etapa autorizada e etapas dependentes de aprovação

**Autorizado nesta fase (2026-10-28):** exclusivamente a criação local deste arquivo na branch `docs/handoff-master`, a partir de `origin/main`.

**Dependem de aprovação explícita e separada:**

1. Commit deste documento.
2. Push da branch `docs/handoff-master`.
3. Abertura de PR.
4. Merge do PR.
5. Merge/deploy do PR #315 (após resolver pendências do §10).
6. Qualquer correção das pendências do §8 (uma por vez, com prova do problema).
7. Atualização/correção de documentos conflitantes (§9).
8. Qualquer ação em Railway, IaC, CORS, PIX, ledger, Asaas, banco ou infraestrutura.

---

## 12. Comandos seguros para retomada do ambiente

Somente leitura; não alteram estado.

```bash
cd /home/dilsondev/dils-wallet
pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short --branch
git log -1 --oneline --decorate origin/main
git stash list                        # apenas listar; nunca aplicar/descartar
sha256sum .railway/railway.ts         # deve começar com 3c729db2
gh pr view 315 --json state,mergeable,mergeStateStatus,headRefOid
```

Atualização de referências remotas locais (não é leitura estrita: grava em `.git/refs/remotes`; não altera branches locais, working tree nem stashes):

```bash
git fetch origin
```

Depois: ler este documento e `docs/AUREA_GOLD_PROJECT_STATE.md`, revalidar contra `origin/main`, definir escopo, testar, `git diff --check` e `git diff`, e pedir autorização para cada etapa.

**Não executar sem autorização:** `git add -A`, `git reset --hard`, `git stash pop/drop/clear`, `git branch -D`, `git push --force`, `git clean`, qualquer comando `railway` que altere estado.

---

## 13. Histórico de atualizações (append-only)

> Adicionar novas entradas ao final. Não editar nem remover entradas anteriores.

| Data | Base `origin/main` | Autor | Alteração |
|---|---|---|---|
| 2026-10-28 | `d85c919a` | Dilson Pereira (com Claude Code) | Criação do documento: 13 seções, reconciliação das 22 pendências, estado do PR #315 e da IaC. Nenhuma alteração de código. |

---

## 14. Continuidade operacional — Railway frontend (2026-11-18)

**Objetivo:** retomar a recuperação do frontend Aurea Gold sem repetir a investigação já concluída.

### Identificação Railway

- Projeto: `sincere-amazement` (`08df05ff-1523-4df8-8ca3-0af2ea296587`).
- Ambiente: `production` (`8469d171-80b7-43a4-b31a-248138052f1a`).
- Serviço frontend: `aurea-gold-client` (`fc70aab8-0e66-4011-b194-1764ba04da2d`).
- Backend: serviço separado `dils-wallet`; não modificar.
- Repositório GitHub: `dilson123-tech/dils-wallet`.
- Root Directory do frontend: `aurea-gold-client`.

### Configuração comprovada

- Frontend React/Vite com Dockerfile próprio.
- Dockerfile utiliza `ARG VITE_API_BASE` e exige valor não vazio durante o build.
- Variável `VITE_API_BASE` identificada no Railway; valor não registrado por segurança.
- Container utiliza porta 8080, compatível com a configuração pública do serviço.
- Healthcheck configurado em `/`.
- Configuração anterior do serviço apresentava Nixpacks/RAILPACK e histórico de `railway.toml` com Nixpacks.
- O `aurea-gold-client/railway.toml` foi corrigido localmente para `builder = "DOCKERFILE"` e `dockerfilePath = "Dockerfile"`.
- Watch Paths: `aurea-gold-client/Dockerfile` existente; `aurea-gold-client/**` preparado adicionalmente na interface.
- A alteração de Watch Paths permanece pendente no Railway. **Não clicar em Apply/Deploy Changes sem autorização específica.**
- Frontend permanece sem recuperação comprovada em produção.
- Conexão do ambiente à branch de publicação ainda não foi concluída.

### Git e validações

- Branch de trabalho: `fix/aurea-client-dockerfile-build`.
- Commits anteriores: `a3be1976` e `d6e3cab4`, restritos ao frontend.
- Commit adicional: `6b731533` — `fix(client): configure Railway Dockerfile builder`.
- `git diff --check` aprovado e pre-commit do commit `6b731533` aprovado.
- Simulação `git merge-tree --write-tree HEAD origin/main` produziu árvore `4ac1efb70eaf2ef39f9a5f18c31b5e3966c20063`, sem conflitos relatados.
- `origin/main` consultada em `d85c919a5f5bdae0fafd628d66d5a042b77f764a`.
- Nenhum push, PR, merge ou deploy desta correção foi realizado nesta sessão.
- Branch documental atual: `docs/handoff-master`; este registro é uma atualização local pendente de revisão e autorização de commit.
- `.railway/` permanece não rastreada e protegida. Não incluir em commit.

### Próximo passo operacional

1. Revisar o diff desta atualização documental; solicitar autorização específica antes de commit e push.
2. Retornar à branch `fix/aurea-client-dockerfile-build` de forma controlada.
3. Preparar a publicação dos três commits do frontend, com autorizações separadas para push, PR e merge.
4. Reconciliar a configuração efetiva do serviço Railway com a configuração versionada, sem alterar backend ou IaC.
5. Somente após autorização explícita, aplicar mudanças de produção e validar deployment, SHA, saúde do serviço e funcionamento visual do frontend.

### Regra permanente de continuidade

Antes de iniciar nova sessão ou investigação, consultar `docs/HANDOFF_MASTER.md`, o Git atual e as evidências já registradas. **Não repetir auditorias, buscas no Railway ou reconstrução de histórico sem divergência nova e comprovada.** Trabalhar somente no delta pendente. Preservar autorizações específicas, especialmente para Git de escrita, Railway, segredos, banco e deploy.

---

## 15. Recuperação do Áurea Gold em produção — 2026-11-19

### Entregas confirmadas

- PR #322: correção de segurança `dnspython` 2.9.0 → 2.9.2, integrado à `main` no commit `30e79a56`.
- PR #321: correções do Dockerfile, contexto de build e configuração Railway do frontend, integrado à `main` no commit `1b79da9b`.
- CI do PR #321: 13 verificações aprovadas, 2 ignoradas e nenhuma falha.
- Railway: serviço `aurea-gold-client` em `production`, com deployment bem-sucedido e status ACTIVE.
- Frontend público: https://aurea-gold-client-production.up.railway.app
- Página de login carregada visualmente; sete requisições de recursos estáticos retornaram HTTP 200.
- Backend público: https://dils-wallet-production.up.railway.app
- Endpoint `/` do backend retornou HTTP 200 com `{"ok":true,"service":"dils-wallet"}`.
- Endpoint `/health` retornou HTTP 404; essa rota não deve ser utilizada como prova de indisponibilidade.
- JavaScript publicado `/assets/index-nA1Fo5Jn.js` contém o endereço HTTPS correto do backend.
- `src/lib/apiBase.ts` prioriza `VITE_API_BASE`, depois `VITE_API_BASE_URL`, com fallback local.
- Dockerfile exige `VITE_API_BASE` não vazia durante o build.

### Configuração Railway confirmada

- Serviço frontend conectado à branch `main`.
- Auto Deploy desativado.
- Root Directory: `aurea-gold-client`.
- Config File: `/aurea-gold-client/railway.toml`.
- Builder configurado como Dockerfile.
- Watch Patterns: `aurea-gold-client/Dockerfile` e `aurea-gold-client/**`.
- Mudanças de configuração aplicadas mediante autorização.
- Backend não foi redeployado durante essa recuperação.

### Pendências reais

1. Validar comunicação efetiva frontend/backend e autenticação, sem operações financeiras reais.
2. Confirmar os resultados de login e chamadas autenticadas antes de declarar recuperação funcional completa.
3. Avaliar posteriormente a migração da configuração Railway para IaC compatível, considerando a descontinuação anunciada de `railway.toml` em 2026-12-01; não modificar `.railway/` sem autorização específica.

### Estado e regras de continuidade

- Esta seção substitui operacionalmente as pendências já resolvidas da seção 14, sem apagar o histórico.
- Branch documental: `docs/handoff-master`.
- `.railway/` permanece não rastreada e protegida.
- Preservar os stashes existentes.
- Não repetir auditorias concluídas; investigar apenas divergências novas e comprovadas.
- Não realizar commit, push, merge, deploy, mudanças no backend, banco, Asaas ou operações financeiras sem autorização específica.
- Esta atualização documental permanece local até revisão do diff e autorização posterior.

---

## 16. Integração controlada e árvore mestre — 2026-11-24

### 16.1. Estado confirmado

- Repositório: dilson123-tech/dils-wallet.
- PR #325 integrado à main.
- Commit: d961c0f4f6212398a789e5f6c1589dabc8c6d959.
- PR #323 integrado à main.
- Commit: 3b85b17e9854ed27d2b574829ddc2b5e8023a806.
- PR #324 permanece BLOQUEADO.
- Dinheiro real permanece desabilitado.
- Nenhum deploy autorizado nesta etapa.

### 16.2. Árvore mestre de desenvolvimento

- [x] AG-01 — Planejamento técnico.
- [x] AG-02 — Implementação do helper monetário.
- [x] AG-03 — Compatibilidade e regressão.
- [x] AG-04 — Commit e publicação do PR #325.
- [x] AG-05 — Validação CI dos PRs.
- [x] AG-06 — Controle de publicação automática.
- [x] AG-07 — Auditoria independente Codex.
- [ ] AG-08 — Integração controlada.
  - [x] Merge do PR #325.
  - [x] Atualização da branch do PR #323.
  - [x] Validação do diff e CI do PR #323.
  - [x] Merge do PR #323.
  - [x] Validação pós-merge do PR #323.
  - [ ] Versionamento desta atualização documental.
  - [ ] Correção e integração segura do PR #324.

### 16.3. Precisão monetária — PR #325

- Helper isolado em backend/app/utils/money.py.
- Conversão Decimal, quantização em centavos e ROUND_HALF_UP.
- 54 testes específicos.
- Suite local: 874 aprovados e 9 ignorados.
- Auditoria Codex: APROVADO COM RESSALVAS.
- Definir precisão e limites determinísticos antes de integrar consumidores.
- Não modificar o formato utilizado pelo hash de preparação Asaas.
- Alterações de zeros decimais podem comprometer idempotência.
- Migração monetária do banco permanece pendente e não autorizada.

### 16.4. Diagnóstico Asaas — PR #323

- Endpoint de status retorna diagnóstico controlado quando
  o adapter Asaas não está registrado.
- provider_adapter_ready=false no cenário indisponível.
- real_money=false nesse cenário.
- HTTP 200 representa sucesso do diagnóstico, não prontidão financeira.
- Erros inesperados continuam sendo propagados.
- Auditoria Codex: APROVADO COM RESSALVAS.
- Corrigir futuramente a semântica de real_money e avaliar
  exceção tipada antes de registrar adapter real.
- Branch atualizada conforme Ruleset 13353521.
- CI anterior ao merge: 16 aprovados, 2 ignorados, zero falhas.
- CI posterior ao merge: 12 workflows concluídos,
  9 aprovados, 3 ignorados, zero falhas.
- Nenhuma publicação GHCR identificada na consulta pós-merge.

### 16.5. PR #324 — BLOQUEIO TÉCNICO

Branch: feat/asaas-sandbox-customer-ensure.
Worktree: ~/dils-wallet-wt/asaas-sandbox-customer.
Baseline local: 5f8ee3d2.

Auditoria Codex: BLOQUEADO.

Correções obrigatórias:

1. Eliminar risco ABA na aquisição e liberação de locks.
2. Utilizar token exclusivo por aquisição.
3. Impedir que concorrentes removam locks de operações ativas.
4. Definir recuperação segura de locks sem expiração automática insegura.
5. Validar rigorosamente paginação, hasMore e totalCount.
6. Não liberar locks após respostas HTTP ambíguas.
7. Liberar somente diante de rejeição definitiva comprovada.
8. Cobrir concorrência real com PostgreSQL local.
9. Testar regressões ABA, remoção indevida de lock,
   paginação inválida e respostas HTTP 4xx.
10. Submeter o delta corrigido à revisão independente Codex.

Condição de avanço: implementação autorizada, testes aprovados,
revisão independente favorável e autorização específica de merge.

Proibidas chamadas financeiras reais e operações em produção.

### 16.6. Controle de publicação

- Workflow GHCR ID 187617251: disabled_manually.
- Railway backend dils-wallet: Auto Deploy desabilitado.
- Railway frontend aurea-gold-client: Auto Deploy desabilitado.
- Serviços observados em estado Sleeping durante a verificação.
- Não reativar publicação sem autorização específica.
- A ausência de workflow GHCR não comprova isoladamente
  a inexistência de outros mecanismos externos de publicação.

### 16.7. Preservação do ambiente

Worktrees preservados:

- ~/dils-wallet
- ~/aurea-gold-clean
- ~/dils-wallet-wt/asaas-sandbox-customer
- ~/dils-wallet-wt/fix-wallet-partner-status
- ~/dils-wallet-wt/handoff-master

O quinto worktree foi criado exclusivamente para documentação.

Preservar os quatro stashes anteriormente identificados.
Preservar alterações locais preexistentes em wallet.py,
test_wallet_partner_status.py e .railway/.

Não aplicar ou descartar stashes.
Não limpar, sobrescrever ou remover worktrees.
Não presumir que referências locais estejam atualizadas.

### 16.8. Governança permanente

- ChatGPT: coordenação técnica e árvore mestre.
- Claude Code: implementação de tarefas complexas autorizadas.
- Codex: revisão independente e validação de segurança.
- Operações simples de Git: execução manual pelo responsável
  no terminal VS Code, um comando por vez.
- Economizar cotas dos agentes.
- Executar etapas previamente autorizadas sem confirmações redundantes.
- Interromper diante de divergência, risco ou operação não autorizada.
- Não repetir auditorias sem evidência nova.
- Atualizar este Handoff após entregas e operações Git autorizadas.
- Não criar documentação redundante.
- Preservar autorizações separadas de commit, push, PR, merge e deploy.

### 16.9. Próxima sequência operacional

1. Revisar a atualização deste Handoff com git diff --check e git diff.
2. Solicitar autorização para commit documental.
3. Solicitar autorização para push documental.
4. Preparar missão de correção do PR #324 no worktree existente.
5. Autorizar implementação delimitada ao bloqueio identificado.
6. Executar testes locais e revisão independente Codex.
7. Integrar somente após aprovação técnica e humana.

Pendências posteriores:

- Migração monetária segura e validada.
- Integração BaaS Asaas condicionada à aprovação comercial.
- Adapter real, KYC/KYB, transferências e reconciliação.
- Avaliação da migração de configuração Railway.
- Validação funcional completa antes de qualquer operação real.

---

## 17. Consolidação estratégica e transferência de continuidade — 24/11/2026

### 17.1. DIRETRIZ PERMANENTE DO PROPRIETÁRIO — PRESERVAÇÃO INTEGRAL DA ESTRATÉGIA

Antes da atual reorganização conduzida pelo ChatGPT, o projeto vinha acumulando implementações, funcionalidades, investigações e estruturas desnecessárias, aumentando a complexidade, o retrabalho, os custos e o prazo de entrega.

A atual coordenação identificou esse problema, corrigiu a direção do desenvolvimento e estabeleceu uma estratégia objetiva, orientada à conclusão de um produto comercial real, seguro e funcional.

O proprietário aprovou expressamente essa reorganização e determina que nenhuma troca de chat, sessão ou agente poderá modificar a estratégia consolidada.

REGRAS PERMANENTES:

- Preservar integralmente a linha de desenvolvimento estabelecida pela atual coordenação.
- Não alterar arquitetura, estratégia, metodologia ou escopo aprovado sem autorização expressa do proprietário.
- Não retornar ao modelo anterior de desenvolvimento excessivo.
- Não reinventar o projeto.
- Não reconstruir componentes que já funcionam corretamente.
- Se já está correto, não mexer.
- Não criar funcionalidades sem necessidade comprovada.
- Não criar estruturas, abstrações ou documentação redundantes.
- Não repetir auditorias, investigações ou implementações concluídas sem justificativa técnica comprovada.
- Trabalhar exclusivamente no delta pendente da árvore mestre.
- Priorizar integração Asaas, confiabilidade financeira, segurança e entrega comercial.
- Não priorizar melhorias cosméticas antes da conclusão funcional.
- Não transformar o projeto em uma plataforma desnecessariamente complexa.
- Consultar obrigatoriamente este Handoff antes de propor novas missões.
- Preservar o trabalho realizado, inclusive alterações locais ainda não commitadas.
- Qualquer mudança estratégica exige autorização expressa do proprietário.

METODOLOGIA OBRIGATÓRIA:

- ChatGPT: coordenação, planejamento e governança.
- Claude Code: implementação de tarefas complexas autorizadas.
- Codex: revisão técnica independente e direcionada.
- Proprietário: autorizações e operações simples no terminal VS Code.
- Economizar cotas dos agentes.
- Operações manuais: um comando por vez, aguardando retorno.
- Agentes: execução autônoma das etapas autorizadas, sem perguntas intermediárias desnecessárias.
- Atualizar este Handoff e a árvore mestre após marcos comprovados.
- Nenhuma autorização crítica pode ser presumida.

A troca de chat não constitui autorização para alterar decisões anteriores.

NÃO ESTAMOS MAIS NA FASE DE INVENTAR O ÁUREA GOLD.
ESTAMOS NA FASE DE TERMINAR O ÁUREA GOLD.

Continuidade significa avançar, não reconstruir.

Esta determinação permanece vigente até alteração expressamente autorizada pelo proprietário.

### 17.2. Resultado AG-08.3 — Correção local do PR #324

Implementação autorizada pelo proprietário e executada pelo Claude Code em 24/11/2026.

Veredito do executor: APROVADO COM RESSALVAS.
Veredito independente: PENDENTE.
PR #324: BLOQUEADO.

Worktree:
    /home/dilsondev/dils-wallet-wt/asaas-sandbox-customer

Branch:
    feat/asaas-sandbox-customer-ensure

HEAD:
    5f8ee3d221ddde141f012b34963608418d25c640

Preflight inicial confirmado: árvore limpa e baseline correspondente à auditoria anterior.

Correções reportadas:

- Lock v2 com token exclusivo por aquisição.
- Token gerado por secrets.token_hex(16).
- Liberação atômica CAS condicionada à chave e ao JSON exato.
- Proteção contra ABA e remoção por proprietário antigo.
- Concorrentes não removem locks alheios.
- Concorrentes com lock ocupado executam somente GET.
- Sem TTL ou expiração automática.
- Validação estrita de data, hasMore, totalCount, limit, offset e deleted.
- Listagem inválida nunca comprova ausência de customer.
- Tratamento conservador de respostas HTTP ambíguas.
- HTTP 400 estruturado seguido de GET vazio tratado pelo executor como rejeição definitiva.
- Demais desfechos ambíguos preservam o lock.
- Sem retry automático de POST.
- Flags fail-closed preservadas.
- Runbook existente atualizado.

Arquivos modificados localmente:

    M backend/app/services/asaas_sandbox_customer_service.py
    M backend/tests/test_asaas_sandbox_customer_ensure.py
    M docs/WALLET_SANDBOX_CYCLE_RUNBOOK.md
    ?? backend/tests/test_asaas_sandbox_customer_concurrency_postgres.py

O arquivo novo de testes ainda não está rastreado.
Deverá ser incluído em eventual commit autorizado.

Resultados reportados pelo Claude Code:

- Suíte sem PostgreSQL: 945 passed, 19 skipped, 0 failed.
- Suíte com PostgreSQL: 961 passed, 3 skipped, 0 failed.
- Testes concorrenciais PostgreSQL: 10/10 aprovados em cinco execuções consecutivas.
- PostgreSQL 18.7 local, isolado e efêmero.
- Conexões independentes e sincronização determinística.
- Dez aquisições simultâneas: exatamente um proprietário.
- Oito chamadas concorrentes: um POST e sete Pending.
- Oito reutilizações posteriores: nenhum POST adicional.
- Proteção ABA comprovada nos testes reportados.
- Teste de mutação: quatro falhas esperadas ao remover condição de token.
- Código original corrigido restaurado com SHA256 idêntico.
- git diff --check: exit 0.
- Tempo reportado: aproximadamente 18 minutos de execução.
- Cluster temporário desligado ao final.

Esses resultados são evidências reportadas pelo executor, não constituindo aprovação independente.

Nenhum commit, push, merge, deploy, chamada real ao Asaas, operação financeira, alteração de segredo, migração ou acesso ao banco de produção foi reportado.

Quatro stashes e demais worktrees preservados.

### 17.3. Árvore mestre atualizada

AG-01 Planejamento: CONCLUÍDO
AG-02 Precisão monetária: CONCLUÍDO
AG-03 Compatibilidade: CONCLUÍDO
AG-04 Publicação do PR: CONCLUÍDO
AG-05 Validação CI: CONCLUÍDO
AG-06 Controle de publicação: CONCLUÍDO
AG-07 Auditoria independente inicial: CONCLUÍDO

AG-08 Integração controlada:
    PR #325: MERGED
    PR #323: MERGED
    CI pós-merge: CONCLUÍDO
    AG-08.3 Implementação local PR #324: CONCLUÍDA COM RESSALVAS
    AG-08.4 Revisão independente Codex: PENDENTE
    AG-08.5 Commit e push da correção: NÃO AUTORIZADOS
    AG-08.6 Validação CI: PENDENTE
    AG-08.7 Merge PR #324: BLOQUEADO

AG-09 Consolidação documental e transferência:
    Diretriz estratégica: APROVADA
    Registro na memória do Claude Code: REPORTADO
    Atualização local do Handoff: AUTORIZADA
    Validação documental: PENDENTE
    Commit documental: PENDENTE DE AUTORIZAÇÃO
    Push documental: PENDENTE DE AUTORIZAÇÃO
    Transferência de chat: PENDENTE

A atualização documental anterior da seção 16 foi commitada e publicada com sucesso:

    Branch: docs/handoff-master
    Commit: c6caec1b

PR #325 integrado na main:
    d961c0f4f6212398a789e5f6c1589dabc8c6d959

PR #323 integrado na main:
    3b85b17e9854ed27d2b574829ddc2b5e8023a806

CI pós-merge #323:
    9 success, 3 skipped, 0 failed, 0 pending.

### 17.4. Ressalvas e bloqueios obrigatórios

A revisão Codex deverá verificar exclusivamente o delta da AG-08.3, incluindo:

- Efetividade da proteção ABA.
- Exclusividade da propriedade e liberação dos locks.
- Segurança da recuperação manual.
- Consistência da paginação.
- Garantia contra POST duplicado.
- Se HTTP 400 estruturado seguido de GET vazio comprova realmente ausência de efeitos remotos, considerando eventual consistência.
- Adequação do contrato de resposta Asaas.
- Qualidade e isolamento dos testes PostgreSQL.
- Se os novos testes concorrenciais serão efetivamente executados no CI.
- Compatibilidade com o fluxo existente.
- Ausência de alterações fora do escopo.

Riscos residuais:

- Locks órfãos exigem recuperação manual.
- Locks inertes podem permanecer no banco.
- Respostas HTTP ambíguas podem exigir intervenção manual.
- Testes PostgreSQL dependem de configuração apropriada.
- A classificação de rejeição definitiva precisa de validação independente.

Travas vigentes:

- PR #324 permanece BLOQUEADO.
- REAL_MONEY_ENABLED=false.
- Nenhuma operação financeira real autorizada.
- Nenhuma alteração em produção autorizada.
- Nenhuma chamada real ao Asaas autorizada nesta missão.
- Nenhum deploy autorizado.
- Nenhuma migração de banco autorizada.
- GHCR workflow 187617251: disabled_manually na última verificação.
- Auto deploy Railway backend e frontend: desabilitados na última verificação.
- Não presumir que todos os mecanismos externos de publicação estejam bloqueados.
- Não reativar mecanismos de publicação sem autorização expressa.

A integração BaaS comercial definitiva com Asaas permanece pendente de confirmação específica.
A resposta comercial genérica recebida não equivale à aprovação do contrato BaaS.

### 17.5. Ponto exato de retomada no próximo chat

PRÓXIMA MISSÃO TÉCNICA: AG-08.4 — Revisão independente Codex.

Antes de iniciar:

1. Ler este Handoff, especialmente as seções 16 e 17.
2. Preservar obrigatoriamente a diretriz estratégica 17.1.
3. Confirmar estado Git do worktree asaas-sandbox-customer.
4. Confirmar HEAD e os quatro arquivos da implementação local.
5. Preparar missão Codex somente leitura, direcionada ao delta corrigido.
6. Obter autorização do proprietário para iniciar a revisão.
7. Aguardar veredito independente antes de autorizar qualquer integração.

Primeiro comando de retomada:

    git -C ~/dils-wallet-wt/asaas-sandbox-customer status --short --branch

Não limpar, descartar, guardar em stash ou sobrescrever as alterações locais.

Não atualizar a branch remotamente, realizar rebase ou merge sem autorização.

Não repetir a auditoria inicial completa.
Não iniciar novas funcionalidades.
Não alterar a estratégia.
Não criar outro Handoff.

O próximo chat deve continuar a missão existente, respeitando integralmente o trabalho, a direção estratégica e as decisões consolidadas.
