# Aurea Gold Wallet - Asaas Sandbox Payment Status Dry Run v1

## Marco

v0.2.45-wallet-asaas-sandbox-payment-status-dry-run

## Status

Este marco adiciona um dry-run seguro para preparacao da consulta de status de pagamento no Asaas Sandbox.

Ele nao executa chamada HTTP, nao consulta status real, nao cria Pix real, nao movimenta saldo e nao usa producao.

## Objetivo

O objetivo e validar que o fluxo de consulta de status de pagamento Sandbox pode ser preparado de forma segura antes de qualquer chamada externa real.

Este marco depende das travas e bases dos marcos v0.2.40, v0.2.41, v0.2.42, v0.2.43 e v0.2.44.

## Arquivos alterados

- backend/app/partner/asaas_client.py
- backend/tests/test_asaas_client_skeleton.py
- docs/WALLET_ASAAS_SANDBOX_PAYMENT_STATUS_DRY_RUN_V1.md

## O que foi adicionado

- AsaasPaymentStatusDryRunResult
- dry_run_get_payment_status
- testes para garantir que o dry-run de status nao executa HTTP
- safe_summary mantendo os flags de seguranca

## Request preparado

O dry-run prepara um request para GET /payments/{id}.

Campo esperado:

- payment_id

## Garantias de seguranca

- nenhuma chamada HTTP e executada
- nenhuma consulta real no Asaas e executada
- nenhum status real e obtido
- nenhuma cobranca Pix real e criada
- nenhum saldo real e movimentado
- producao continua bloqueada
- real_money=false
- http_call_executed=false
- ready_for_http_execution=false
- API Key real nao deve ser usada
- webhook token real nao deve ser usado
- Wallet ID real nao deve ser usado
- safe_summary nao expoe segredos

## Fora de escopo

- chamada real para o Asaas Sandbox
- chamada para producao
- consulta real de status
- obtencao real de QR Code Pix
- criacao real de cobranca Pix
- webhook real
- conciliacao real
- saldo real
- BaaS real
- subconta real
- split real

## Validacao local

Comando:

cd backend && pytest tests/test_asaas_client_skeleton.py tests/test_asaas_config_guards.py -q

Resultado esperado:

25 passed

## Proximo passo provavel

v0.2.46-wallet-asaas-sandbox-full-dry-run-flow

Esse proximo marco deve preparar o fluxo dry-run completo cliente -> cobranca Pix -> QR Code -> status, ainda sem chamada HTTP real e sem dinheiro real.
