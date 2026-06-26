# Aurea Gold — Preflight do Spike Técnico Asaas Sandbox v1

Status: draft
Marco planejado: v0.2.35-wallet-asaas-sandbox-technical-spike-preflight
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Natureza: produto real/comercial, não projeto de estudo.

## 1. Objetivo

Este documento define a checagem prévia obrigatória antes do primeiro spike técnico com código usando o Asaas Sandbox.

O objetivo é garantir que a integração futura só comece quando houver segurança suficiente sobre ambiente, credenciais, URL base, webhooks, logs e bloqueio absoluto de produção.

Este marco ainda não implementa integração.

## 2. Regra central

Nenhum código de integração Asaas deve ser iniciado sem passar por este preflight.

Este documento não autoriza:

- Pix real;
- saldo real;
- cobrança real;
- subconta real;
- split real;
- transferência real;
- operação financeira produtiva;
- uso de credencial de produção;
- token real no Git;
- API key real no Git.

## 3. Base documental anterior

Este preflight se apoia nos documentos:

- `docs/WALLET_PARTNER_CONTACT_LOG_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_VALIDATION_PLAN_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_READINESS_CHECKLIST_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PLAN_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_ACCESS_NOTES_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_ACCESS_CONFIRMATION_NOTES_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_API_WEBHOOK_NOTES_V1.md`
- `docs/WALLET_SANDBOX_CYCLE_RUNBOOK.md`

## 4. Estado atual confirmado

Itens já confirmados:

- [x] Asaas segue como parceiro candidato Prioridade A.
- [x] Acesso ao painel Asaas foi realizado.
- [x] Ambiente Sandbox foi localizado.
- [x] Conta Sandbox já existente foi acessada.
- [x] Dashboard Sandbox carregou com sucesso.
- [x] Saldo Sandbox apareceu como R$ 0,00.
- [x] Áreas de Pix, Cobranças, Clientes e Links de Pagamento foram localizadas.
- [x] Áreas de Chaves de API, Segurança, Webhooks e Logs foram vistas no painel de integrações.
- [x] Nenhuma credencial foi registrada no Git.
- [x] Nenhuma operação real foi realizada.

## 5. Pendências antes de código

Antes de iniciar qualquer código, ainda precisa estar confirmado:

- [ ] Chave de API Sandbox existente, sem expor valor.
- [ ] Chave de API Sandbox armazenada fora do Git.
- [ ] URL base oficial do Sandbox identificada.
- [ ] Documentação oficial da API localizada.
- [ ] Padrão de autenticação entendido.
- [ ] Endpoint de criação de cobrança localizado.
- [ ] Endpoint de cobrança Pix localizado.
- [ ] Endpoint de consulta de cobrança localizado.
- [ ] Configuração de webhook Sandbox entendida.
- [ ] Validação do header `asaas-access-token` entendida.
- [ ] Logs de requisições entendidos.
- [ ] Logs de webhooks entendidos.
- [ ] Separação entre Sandbox e produção clara.
- [ ] Risco de usar produção por engano eliminado.

## 6. Variáveis planejadas para ambiente local

Variáveis previstas para um futuro spike técnico:

- `ASAAS_ENV=sandbox`
- `ASAAS_BASE_URL`
- `ASAAS_API_KEY`
- `ASAAS_WEBHOOK_TOKEN`
- `ASAAS_WEBHOOK_ALLOWED_IPS`
- `WALLET_PARTNER_PROVIDER=asaas`
- `WALLET_MODE=partner`
- `REAL_MONEY_ENABLED=false`

Regras:

- nenhuma variável real deve ser registrada neste documento;
- nenhum valor real deve ser commitado;
- `.env` deve continuar fora do Git;
- `.env.example` pode conter apenas nomes de variáveis, sem valores reais;
- logs devem mascarar qualquer segredo;
- produção deve permanecer bloqueada por configuração e por regra de negócio.

## 7. Arquivos candidatos para um spike futuro

Arquivos que poderão ser avaliados em marco futuro, sem obrigação de alteração neste preflight:

- `backend/app/config.py`
- `backend/app/api/v1/routes/wallet.py`
- `backend/app/models/idempotency.py`
- `docs/WALLET_SANDBOX_CYCLE_RUNBOOK.md`

Se necessário, novos arquivos futuros devem isolar o Asaas Sandbox da operação produtiva.

Possíveis arquivos futuros:

- adapter Asaas Sandbox;
- service de cobrança Sandbox;
- validador de webhook Sandbox;
- testes de configuração;
- testes de idempotência;
- testes de bloqueio de produção.

## 8. Testes mínimos exigidos no spike futuro

O primeiro spike com código só deve ser aceito se tiver testes para:

- configuração Sandbox;
- bloqueio quando `ASAAS_ENV` não for `sandbox`;
- bloqueio quando `REAL_MONEY_ENABLED` não for `false`;
- ausência de credencial em logs;
- validação de webhook por token;
- idempotência/replay de webhook;
- não alteração de saldo real;
- não geração de comprovante real;
- não uso de endpoint produtivo.

## 9. Critérios de abortar o spike

O spike técnico deve ser abortado imediatamente se:

- houver dúvida entre Sandbox e produção;
- a credencial usada parecer de produção;
- a URL base parecer produtiva;
- logs exibirem token ou API key;
- webhook não puder ser validado com segurança;
- documentação estiver insuficiente;
- qualquer chamada puder movimentar dinheiro real;
- qualquer código tentar alterar saldo real;
- qualquer código tentar gerar comprovante real;
- qualquer segredo aparecer em arquivo versionado.

## 10. Critérios para liberar o primeiro código

O próximo marco poderá iniciar código somente se:

- Chave de API Sandbox estiver segura fora do Git;
- URL base Sandbox estiver confirmada;
- endpoints mínimos estiverem identificados;
- webhook Sandbox estiver entendido;
- token de webhook puder ser validado;
- logs estiverem sob controle;
- produção estiver explicitamente bloqueada;
- houver plano de testes mínimo;
- houver decisão explícita de avançar apenas em Sandbox.

## 11. Resultado esperado deste marco

Ao final deste marco, o repositório deve conter apenas documentação.

Entregáveis:

- preflight do spike técnico;
- pendências antes de código;
- variáveis planejadas;
- arquivos candidatos;
- testes mínimos exigidos;
- critérios de abortar;
- critérios para liberar código;
- nenhum token;
- nenhuma API key;
- nenhum segredo;
- nenhuma integração real.

## 12. Próximo marco provável

Se o preflight for aprovado, o próximo marco poderá ser:

- `v0.2.36-wallet-asaas-sandbox-env-example`

Ou, se ainda faltar confirmação no painel/documentação:

- `v0.2.36-wallet-asaas-sandbox-api-webhook-followup-notes`

O primeiro código de integração só deve vir depois de ambiente, credenciais e bloqueios estarem claramente definidos.
