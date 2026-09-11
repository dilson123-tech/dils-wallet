# Aurea Gold / dils-wallet — Asaas Sandbox Config Guards V1

Marco planejado: v0.2.40-wallet-asaas-sandbox-config-guards

Status: primeiro codigo seguro da integracao Asaas Sandbox.

Este marco adiciona guardas de configuracao para a integracao Asaas Sandbox.

Nao ha chamada HTTP neste marco.

Nao ha Pix real neste marco.

Nao ha saldo real neste marco.

Nao ha producao neste marco.

Nao ha API Key real, token real ou Wallet ID real no Git.

## 1. Objetivo

Criar uma camada pequena e testavel para validar se a configuracao local do Asaas Sandbox esta segura antes de qualquer futura chamada de API.

O objetivo principal e impedir uso acidental de producao, dinheiro real ou segredo em local inseguro.

## 2. Arquivos criados ou alterados

Arquivos criados:

- backend/app/partner/asaas_config.py
- backend/tests/test_asaas_config_guards.py
- docs/WALLET_ASAAS_SANDBOX_CONFIG_GUARDS_V1.md

Arquivo alterado:

- backend/.env.example

## 3. Guardas implementadas

A funcao load_asaas_sandbox_config valida:

- WALLET_MODE=partner
- WALLET_PARTNER_PROVIDER=asaas
- REAL_MONEY_ENABLED=false
- ASAAS_ENV=sandbox
- ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3
- ASAAS_API_KEY configurada fora do Git
- ASAAS_WEBHOOK_TOKEN configurado fora do Git

A configuracao e rejeitada se:

- WALLET_MODE nao for partner;
- WALLET_PARTNER_PROVIDER nao for asaas;
- REAL_MONEY_ENABLED estiver true;
- ASAAS_ENV nao for sandbox;
- ASAAS_BASE_URL apontar para producao;
- ASAAS_BASE_URL nao for a URL Sandbox oficial;
- ASAAS_API_KEY estiver vazia ou com placeholder;
- ASAAS_WEBHOOK_TOKEN estiver vazio ou com placeholder.

## 4. Bloqueio contra producao

A URL de producao do Asaas e explicitamente bloqueada:

https://api.asaas.com/v3

A URL Sandbox oficial permitida e:

https://sandbox.asaas.com/api/v3

## 5. Segredos protegidos

O modulo Asaas Sandbox nao deve expor segredo em representacao textual.

O metodo __repr__ mascara:

- api_key
- webhook_token

O metodo safe_summary informa apenas se os valores foram configurados, sem mostrar o conteudo.

## 6. Sem chamada externa

Este marco nao cria cliente HTTP.

Este marco nao chama API do Asaas.

Este marco nao cria cliente pagador.

Este marco nao cria cobranca Pix.

Este marco nao consulta QR Code.

Este marco nao recebe webhook real.

Este marco apenas prepara as travas de seguranca.

## 7. Testes adicionados

Teste criado:

- backend/tests/test_asaas_config_guards.py

Cenarios cobertos:

- aceita configuracao Sandbox segura;
- nao vaza API Key no repr;
- nao vaza webhook token no repr;
- rejeita WALLET_MODE incorreto;
- rejeita WALLET_PARTNER_PROVIDER incorreto;
- rejeita REAL_MONEY_ENABLED=true;
- rejeita ASAAS_ENV=production;
- rejeita URL de producao;
- rejeita URL desconhecida;
- rejeita API Key placeholder;
- rejeita webhook token placeholder;
- normaliza barra final na URL Sandbox.

## 8. Validacao local

Comando executado:

pytest tests/test_asaas_config_guards.py -q

Resultado esperado:

11 passed

## 9. Atualizacao do backend/.env.example

O backend/.env.example foi atualizado para registrar a URL Sandbox oficial confirmada pelo Asaas:

ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3

O arquivo continua sem segredo real.

Os campos sensiveis permanecem com placeholders seguros:

- ASAAS_API_KEY
- ASAAS_WEBHOOK_TOKEN

## 10. Criterios de sucesso

Este marco e considerado concluido quando:

- os arquivos forem criados;
- backend/.env.example continuar sem segredo real;
- pytest do teste Asaas passar;
- git diff --check passar;
- o PR passar nos checks;
- o PR for mergeado;
- a tag oficial for criada.

Tag esperada:

v0.2.40-wallet-asaas-sandbox-config-guards

## 11. Proximo marco provavel

Proximo marco provavel:

v0.2.41-wallet-asaas-sandbox-client-skeleton

Esse proximo marco pode criar o esqueleto do cliente Asaas Sandbox, ainda com cuidado para nao executar chamada real sem travas aprovadas.
