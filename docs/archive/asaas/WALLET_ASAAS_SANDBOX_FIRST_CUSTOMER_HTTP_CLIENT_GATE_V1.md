# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Client Gate V1

Milestone: v0.2.50-wallet-asaas-sandbox-first-customer-http-client-gate

## Purpose

This milestone adds a technical client gate for the first future Asaas Sandbox customer HTTP call.

The gate prepares the exact customer request for POST /customers, recognizes the mandatory manual authorization phrase, and keeps the HTTP transport disabled.

## Safety status

This milestone does not execute HTTP.

It does not send any request to Asaas, create a customer, create a Pix charge, retrieve a Pix QR Code, check payment status, use production, move real money, expose API Key, expose webhook token or expose Wallet ID.

## First HTTP call target

The planned first external Sandbox call remains:

- Method: POST
- Path: /customers
- Operation: create_customer
- Base URL: https://sandbox.asaas.com/api/v3
- Environment: sandbox

## Added code

The milestone adds:

- AsaasFirstCustomerHttpClientGateResult
- AsaasSandboxClient.gate_first_customer_http_call

The gate reuses the existing prepare_create_customer request builder.

## Gate behavior

The gate:

- prepares the customer request metadata;
- checks whether the manual authorization phrase was provided;
- keeps http_transport_enabled=false;
- keeps ready_for_http_execution=false;
- keeps http_call_executed=false;
- keeps real_money=false;
- returns only a safe summary.

## Manual authorization phrase

The gate recognizes the phrase:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

Recognizing the phrase does not execute HTTP and does not enable the HTTP transport.

## Safe summary behavior

The safe summary reports:

- operation;
- customer reference;
- prepared request summary;
- manual authorization status;
- HTTP transport status;
- real money status;
- HTTP execution status;
- next required step.

The safe summary does not include API Key, webhook token, Wallet ID, headers or raw secrets.

## Tests added

The tests confirm that:

- the gate prepares POST /customers;
- the customer payload is preserved;
- no HTTP call is executed;
- real money remains disabled;
- HTTP transport remains disabled;
- the manual phrase can be recognized;
- ready_for_http_execution remains false;
- safe summary does not leak secrets.

## Validation

Validated locally with:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Result:

32 passed

## Out of scope

This milestone does not implement a real HTTP transport, does not call Asaas, does not create a customer, does not create Pix, does not retrieve QR Code, does not consult status, does not enable production and does not enable real money.

## Next likely milestone

v0.2.51-wallet-asaas-sandbox-first-customer-http-transport-review
