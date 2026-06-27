# Aurea Gold Wallet - Asaas Sandbox Payment Dry Run v1

## Marco

v0.2.43-wallet-asaas-sandbox-payment-dry-run

## Status

Este marco adiciona um dry-run seguro para preparacao de cobranca Pix no Asaas Sandbox.

Ele nao executa chamada HTTP, nao cria cobranca Pix real, nao movimenta saldo e nao usa producao.

## Objetivo

O objetivo e validar que o fluxo de criacao de cobranca Pix Sandbox pode ser preparado de forma segura antes de qualquer chamada externa real.

Este marco depende das travas e bases dos marcos v0.2.40, v0.2.41 e v0.2.42.

## Arquivos alterados

- backend/app/partner/asaas_client.py
- backend/tests/test_asaas_client_skeleton.py
- docs/WALLET_ASAAS_SANDBOX_PAYMENT_DRY_RUN_V1.md

## O que foi adicionado

- AsaasPaymentDryRunResult
- dry_run_create_pix_payment
- testes para garantir que o dry-run Pix nao executa HTTP
- safe_summary mantendo os flags de seguranca

## Request preparado

O dry-run prepara um request para POST /payments.

Campos preparados:

- customer
- billingType=PIX
- value
- dueDate
- description

## Garantias de seguranca

- nenhuma chamada HTTP e executada
- nenhuma cobranca Pix real e criada
- nenhum QR Code Pix real e gerado
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
- criacao real de cobranca Pix
- QR Code Pix real
- consulta real de status
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

21 passed

## Proximo passo provavel

v0.2.44-wallet-asaas-sandbox-pix-qr-code-dry-run

Esse proximo marco deve preparar o dry-run de obtencao do QR Code Pix Sandbox, ainda sem chamada HTTP real e sem dinheiro real.
