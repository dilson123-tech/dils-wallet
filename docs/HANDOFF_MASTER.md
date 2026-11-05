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
