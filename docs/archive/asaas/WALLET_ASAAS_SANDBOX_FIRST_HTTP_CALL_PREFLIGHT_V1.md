# Aurea Gold Wallet — Asaas Sandbox First HTTP Call Preflight V1

Milestone: v0.2.49-wallet-asaas-sandbox-first-http-call-preflight

## Purpose

This milestone adds a local preflight validation before the first real HTTP call to the Asaas Sandbox.

The preflight confirms that the local environment is safe before any future external Sandbox call is manually executed.

## Safety status

This milestone does not execute HTTP.

It does not send requests to Asaas, create a customer, create a Pix charge, retrieve a Pix QR Code, check a real payment status, use production, move real money, expose API keys, expose webhook tokens or expose Wallet IDs.

## First HTTP call target

The planned first external Sandbox call remains:

- Method: POST
- Path: /customers
- Operation: create_customer
- Base URL: https://sandbox.asaas.com/api/v3
- Environment: sandbox

This target is safer than starting with Pix charge creation, Pix QR Code retrieval, payment status lookup, wallet movement, split, subaccount or production behavior.

## Added code

The milestone adds:

- ASAAS_SANDBOX_MANUAL_AUTHORIZATION_PHRASE
- AsaasFirstHttpCallPreflightResult
- run_asaas_first_http_call_preflight

The preflight reuses the strict Asaas Sandbox configuration guards already present in load_asaas_sandbox_config.

## Validated environment rules

The preflight requires:

- WALLET_MODE=partner
- WALLET_PARTNER_PROVIDER=asaas
- REAL_MONEY_ENABLED=false
- ASAAS_ENV=sandbox
- ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3
- ASAAS_API_KEY configured outside Git
- ASAAS_WEBHOOK_TOKEN configured outside Git
- production base URL blocked
- placeholder secrets blocked

## Manual authorization phrase

Required phrase:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

The preflight can recognize whether this phrase was provided, but it still does not allow automatic HTTP execution.

## Safe summary behavior

The preflight safe summary reports the operation, target method, target path, target operation, safe environment summary, manual authorization status, real_money=false, http_call_executed=false, ready_for_http_execution=false and the next required step.

The summary does not include API Key, webhook token, Wallet ID, headers, raw secrets or production credentials.

## Tests added

The test suite confirms that safe Sandbox environment is accepted, the first target is POST /customers, no HTTP is executed, real money remains disabled, manual authorization can be recognized, HTTP remains blocked after authorization recognition, production URL is rejected before any HTTP call and safe summary does not leak secrets.

## Validation

Validated locally with:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Result:

30 passed

## Out of scope

This milestone does not implement a real HTTP transport, execute the first Sandbox call, create a real Asaas customer, create a Pix payment, retrieve a Pix QR Code, check payment status, enable production, enable real money, store secrets or print secrets.

## Next likely milestone

v0.2.50-wallet-asaas-sandbox-first-customer-http-client-gate
