# Aurea Gold Wallet - Asaas Sandbox Customer Dry Run v1

## Marco

v0.2.42-wallet-asaas-sandbox-customer-dry-run

## Status

Este marco adiciona um dry-run seguro para criacao de cliente pagador no Asaas Sandbox.

Ele nao executa chamada HTTP, nao cria cliente real, nao cria Pix real, nao movimenta saldo e nao usa producao.

## Objetivo

O objetivo e validar que o fluxo de criacao de cliente Sandbox pode ser preparado de forma segura antes de qualquer chamada externa real.

Este marco depende das travas dos marcos v0.2.40 e v0.2.41.

## Arquivos alterados

- backend/app/partner/asaas_client.py
- backend/tests/test_asaas_client_skeleton.py
- docs/WALLET_ASAAS_SANDBOX_CUSTOMER_DRY_RUN_V1.md

## O que foi adicionado

- AsaasCustomerDryRunResult
- dry_run_create_customer
- testes para garantir que o dry-run nao executa HTTP
- safe_summary mantendo os flags de seguranca

## Request preparado

O dry-run prepara um request para POST /customers.

Campos preparados:

- name
- cpfCnpj
- email
- mobilePhone

## Garantias de seguranca

- nenhuma chamada HTTP e executada
- nenhum cliente real e criado
- nenhum Pix real e criado
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
- persistencia de cliente no banco
- criacao real de cobranca Pix
- QR Code Pix real
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

19 passed

## Proximo passo provavel

v0.2.43-wallet-asaas-sandbox-payment-dry-run

Esse proximo marco deve preparar o dry-run de uma cobranca Pix Sandbox, ainda sem chamada HTTP real e sem dinheiro real.
