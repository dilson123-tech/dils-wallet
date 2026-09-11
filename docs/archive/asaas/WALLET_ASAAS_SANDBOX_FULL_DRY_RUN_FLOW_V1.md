# Aurea Gold Wallet - Asaas Sandbox Full Dry Run Flow v1

## Marco

v0.2.46-wallet-asaas-sandbox-full-dry-run-flow

## Status

Este marco adiciona um fluxo completo de dry-run seguro para o Asaas Sandbox.

Ele prepara, em sequencia, os passos de cliente, cobranca Pix, QR Code Pix e consulta de status.

Ele nao executa chamada HTTP, nao cria cliente real, nao cria cobranca Pix real, nao obtem QR Code Pix real, nao consulta status real, nao movimenta saldo e nao usa producao.

## Objetivo

O objetivo e validar que o fluxo tecnico completo do primeiro Pix Sandbox pode ser montado de ponta a ponta antes de qualquer chamada externa real.

Este marco consolida os dry-runs criados nos marcos anteriores:

- v0.2.42: customer dry-run
- v0.2.43: payment dry-run
- v0.2.44: Pix QR Code dry-run
- v0.2.45: payment status dry-run

## Arquivos alterados

- backend/app/partner/asaas_client.py
- backend/tests/test_asaas_client_skeleton.py
- docs/WALLET_ASAAS_SANDBOX_FULL_DRY_RUN_FLOW_V1.md

## O que foi adicionado

- AsaasFullDryRunFlowResult
- dry_run_full_pix_flow
- testes para garantir que o fluxo completo nao executa HTTP
- safe_summary consolidado para todos os passos do fluxo

## Fluxo preparado

O fluxo completo prepara estes passos:

1. POST /customers
2. POST /payments
3. GET /payments/{id}/pixQrCode
4. GET /payments/{id}

## Campos de entrada do dry-run

- name
- cpf_cnpj
- email
- mobile_phone
- value
- due_date
- description
- sandbox_customer_id
- sandbox_payment_id

## Garantias de seguranca

- nenhuma chamada HTTP e executada
- nenhum cliente real e criado
- nenhuma cobranca Pix real e criada
- nenhum QR Code Pix real e obtido
- nenhum status real e consultado
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
- criacao real de cliente
- criacao real de cobranca Pix
- obtencao real de QR Code Pix
- consulta real de status
- webhook real
- conciliacao real
- saldo real
- BaaS real
- subconta real
- split real
- transferencia real

## Validacao local

Comando:

cd backend && pytest tests/test_asaas_client_skeleton.py tests/test_asaas_config_guards.py -q

Resultado esperado:

27 passed

## Proximo passo provavel

v0.2.47-wallet-asaas-sandbox-manual-execution-gate

Esse proximo marco deve preparar uma trava/documentacao de autorizacao manual antes de qualquer chamada HTTP real no Sandbox.
