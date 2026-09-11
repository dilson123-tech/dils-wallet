# Aurea Gold — Notas de API e Webhook do Asaas Sandbox v1

Status: draft
Marco planejado: v0.2.34-wallet-asaas-sandbox-api-webhook-notes
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Natureza: produto real/comercial, não projeto de estudo.

## 1. Objetivo

Este documento registra as notas iniciais sobre API, Webhooks, Logs e documentação técnica do Asaas Sandbox.

O objetivo é confirmar onde ficam as áreas técnicas necessárias para um futuro spike controlado, sem registrar credenciais, tokens, senhas, Wallet ID ou qualquer segredo.

Este marco ainda não implementa integração.

## 2. Regra central de segurança

Este documento não registra e nunca deve registrar:

- API key;
- token;
- senha;
- segredo;
- Wallet ID;
- chave Pix real;
- QR Code real;
- payload sensível;
- print com credencial;
- dado bancário real;
- dado de cliente real;
- URL com credencial.

## 3. Base documental anterior

Este documento complementa:

- `docs/WALLET_PARTNER_CONTACT_LOG_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_VALIDATION_PLAN_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_READINESS_CHECKLIST_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PLAN_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_ACCESS_NOTES_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_ACCESS_CONFIRMATION_NOTES_V1.md`
- `docs/WALLET_SANDBOX_CYCLE_RUNBOOK.md`

## 4. Áreas técnicas vistas no painel

Durante a verificação manual, foram vistas áreas técnicas relacionadas a integrações.

Áreas localizadas:

- Chaves de API.
- Segurança.
- Webhooks.
- Logs de Requisições.
- Logs de Webhooks.

Essas áreas ainda precisam ser analisadas com cuidado antes de qualquer código.

## 5. Chaves de API

Status: pendente de confirmação segura.

Objetivo da próxima verificação:

- confirmar se existe chave específica de Sandbox;
- confirmar onde a chave é exibida;
- confirmar se há botão para gerar ou copiar chave;
- confirmar se a chave pode ser revogada;
- confirmar se a chave fica separada da produção;
- confirmar se há instruções de uso na documentação.

Regras:

- não copiar chave para o chat;
- não copiar chave para Markdown;
- não salvar chave no Git;
- não colocar chave em issue;
- não colocar chave em PR;
- não colocar chave em print;
- guardar chave somente em ambiente local seguro.

## 6. Webhooks

Status: pendente de confirmação segura.

Objetivo da próxima verificação:

- confirmar onde criar webhook;
- confirmar se webhook pode ser configurado no Sandbox;
- confirmar eventos disponíveis;
- confirmar se existe token de validação;
- confirmar uso do header `asaas-access-token`;
- confirmar se há logs de entrega;
- confirmar se há opção de reenvio;
- confirmar se há documentação pública.

Regras:

- não registrar token real;
- não registrar URL com segredo;
- não registrar payload sensível;
- não registrar print com segredo;
- não usar endpoint produtivo.

## 7. Logs de requisições

Status: pendente de confirmação segura.

Objetivo da próxima verificação:

- confirmar se há logs separados para Sandbox;
- confirmar se logs mostram endpoint chamado;
- confirmar se logs mostram status HTTP;
- confirmar se logs expõem payload;
- confirmar se logs mascaram credenciais;
- confirmar se logs podem ajudar no spike técnico.

Risco:

Se os logs exibirem token, API key ou payload sensível, não devem ser registrados em print, Markdown, issue ou PR.

## 8. Logs de webhooks

Status: pendente de confirmação segura.

Objetivo da próxima verificação:

- confirmar se há logs de eventos enviados;
- confirmar se há status de entrega;
- confirmar se há corpo da requisição;
- confirmar se há headers;
- confirmar se existe reenvio de webhook;
- confirmar se existe filtro por evento.

Risco:

Se os logs exibirem token, headers sensíveis ou dados pessoais, não devem ser copiados para o repositório.

## 9. URL base Sandbox

Status: pendente de confirmação.

Itens a confirmar:

- URL base oficial da API Sandbox;
- separação clara entre Sandbox e produção;
- documentação oficial da URL base;
- padrão de autenticação;
- padrão de erros;
- endpoints mínimos para cobrança;
- endpoints mínimos para consulta;
- endpoints mínimos para webhook.

Nenhuma URL com credencial deve ser registrada.

## 10. Endpoints mínimos candidatos

Endpoints ou categorias a localizar na documentação oficial:

- criação de cobrança;
- cobrança Pix;
- consulta de cobrança;
- webhooks;
- logs;
- extrato;
- histórico;
- subcontas, se disponível em Sandbox;
- split, se disponível em Sandbox.

Os endpoints exatos ainda devem ser confirmados na documentação oficial antes de qualquer código.

## 11. Pendências antes do spike com código

Antes de iniciar código, ainda falta confirmar:

- [ ] Chave de API Sandbox sem expor valor.
- [ ] URL base Sandbox.
- [ ] Documentação oficial da API.
- [ ] Como autenticar requisições.
- [ ] Como criar cobrança Pix Sandbox.
- [ ] Como consultar cobrança Sandbox.
- [ ] Como configurar webhook Sandbox.
- [ ] Como validar `asaas-access-token`.
- [ ] Como consultar logs de requisições.
- [ ] Como consultar logs de webhooks.
- [ ] Se subcontas existem no Sandbox.
- [ ] Se split existe no Sandbox.
- [ ] Se há risco de confundir Sandbox com produção.

## 12. Bloqueios de produção

Mesmo com Sandbox acessível, continua proibido:

- Pix real;
- saldo real;
- cobrança real;
- subconta real;
- split real;
- transferência real;
- operação financeira produtiva;
- uso de credencial de produção;
- credencial real no Git;
- token real no Git.

## 13. Critério para próximo marco

O próximo marco só deve avançar para código se:

- a chave Sandbox estiver segura fora do Git;
- a URL base Sandbox estiver confirmada;
- os endpoints mínimos forem identificados;
- o webhook Sandbox estiver entendido;
- a validação por token estiver clara;
- os logs não expuserem segredo de forma insegura;
- produção continuar explicitamente bloqueada.

## 14. Próximo marco provável

Se as informações forem confirmadas com segurança, o próximo marco poderá ser:

- `v0.2.35-wallet-asaas-sandbox-technical-spike-preflight`

Ou, se ainda faltar informação:

- `v0.2.35-wallet-asaas-sandbox-api-webhook-followup-notes`
