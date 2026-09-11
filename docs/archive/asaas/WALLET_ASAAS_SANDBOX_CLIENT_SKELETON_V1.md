# Aurea Gold / dils-wallet — Asaas Sandbox Client Skeleton V1

Marco planejado: v0.2.41-wallet-asaas-sandbox-client-skeleton

Status: esqueleto seguro do cliente Asaas Sandbox.

Este marco cria o esqueleto do cliente Asaas Sandbox sem executar chamadas HTTP.

Nao ha Pix real neste marco.

Nao ha saldo real neste marco.

Nao ha producao neste marco.

Nao ha API Key real, token real ou Wallet ID real no Git.

## 1. Objetivo

Criar uma camada inicial para preparar requisicoes do fluxo Asaas Sandbox, usando as guardas de seguranca criadas no marco anterior.

O objetivo deste marco e organizar o cliente tecnico antes de qualquer chamada real para o Sandbox.

## 2. Arquivos criados

Arquivos criados:

- backend/app/partner/asaas_client.py
- backend/tests/test_asaas_client_skeleton.py
- docs/WALLET_ASAAS_SANDBOX_CLIENT_SKELETON_V1.md

## 3. Relacao com o marco anterior

Este marco depende das guardas criadas em:

v0.2.40-wallet-asaas-sandbox-config-guards

O cliente Asaas Sandbox usa:

- AsaasSandboxConfig
- load_asaas_sandbox_config

Assim, qualquer uso sem configuracao segura deve falhar antes de preparar integracao real.

## 4. O que o cliente prepara

O cliente cria metadados seguros para os seguintes fluxos:

- criar cliente pagador Sandbox;
- criar cobranca Pix Sandbox;
- obter QR Code Pix Sandbox;
- consultar status de pagamento Sandbox.

Endpoints preparados:

- POST /v3/customers
- POST /v3/payments
- GET /v3/payments/{id}/pixQrCode
- GET /v3/payments/{id}

## 5. Sem chamada HTTP

Este marco nao executa HTTP.

O metodo execute_prepared_request bloqueia execucao e levanta erro intencional.

A estrutura AsaasPreparedRequest registra:

- method;
- url;
- operation;
- json;
- headers_configured;
- real_money=false;
- http_call_executed=false.

## 6. Seguranca

O cliente foi criado com as seguintes regras:

- nao chama API do Asaas;
- nao cria cobranca real;
- nao cria cliente real;
- nao consulta QR Code real;
- nao consulta status real;
- nao movimenta dinheiro;
- nao libera saldo;
- nao gera comprovante real;
- nao loga API Key;
- nao loga token de webhook.

## 7. Testes adicionados

Teste criado:

- backend/tests/test_asaas_client_skeleton.py

Cenarios cobertos:

- prepara criacao de cliente Sandbox sem chamada HTTP;
- prepara cobranca Pix Sandbox sem chamada HTTP;
- prepara consulta de QR Code Pix sem chamada HTTP;
- prepara consulta de status sem chamada HTTP;
- bloqueia execucao HTTP neste marco;
- safe_summary nao expoe API Key;
- safe_summary nao expoe webhook token.

## 8. Validacao local

Comando executado:

pytest tests/test_asaas_client_skeleton.py tests/test_asaas_config_guards.py -q

Resultado esperado:

17 passed

## 9. Fora de escopo

Nao faz parte deste marco:

- chamada real ao Asaas Sandbox;
- chamada real ao Asaas producao;
- criacao real de cliente;
- criacao real de cobranca Pix;
- confirmacao real de pagamento;
- webhook real;
- conciliacao real;
- saldo real;
- Pix real;
- subconta real;
- split real;
- transferencia real.

## 10. Criterios de sucesso

Este marco e considerado concluido quando:

- o cliente skeleton estiver criado;
- os testes passarem;
- o cliente nao executar HTTP;
- git diff --check passar;
- o PR passar nos checks;
- o PR for mergeado;
- a tag oficial for criada.

Tag esperada:

v0.2.41-wallet-asaas-sandbox-client-skeleton

## 11. Proximo marco provavel

Proximo marco provavel:

v0.2.42-wallet-asaas-sandbox-customer-dry-run

Esse proximo marco pode preparar um dry-run mais explicito para cliente pagador Sandbox, ainda sem expor segredo e sem dinheiro real.
