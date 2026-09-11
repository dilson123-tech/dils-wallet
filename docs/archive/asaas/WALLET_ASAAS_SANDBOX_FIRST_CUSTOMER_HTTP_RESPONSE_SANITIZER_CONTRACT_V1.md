# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Response Sanitizer Contract V1

Milestone: v0.2.55-wallet-asaas-sandbox-first-customer-http-response-sanitizer-contract

## Purpose

This milestone adds a response sanitizer contract for the future first Asaas Sandbox POST /customers HTTP call.

The sanitizer contract defines which fields may be safely exposed from a future provider response and which fields must always remain blocked.

This milestone still does not implement a real HTTP adapter and does not send any request to Asaas.

## Confirmed Asaas target

The target remains:

- Base URL: https://sandbox.asaas.com/api/v3
- Method: POST
- Path: /customers
- Operation: create_customer
- Authentication header name: access_token
- Environment: sandbox

## What changed

Added:

- AsaasFirstCustomerHttpResponseSanitizerContractResult
- build_first_customer_http_response_sanitizer_contract
- success response sanitizer contract
- error response sanitizer contract
- tests proving the sanitizer contract remains blocked
- tests proving manual authorization does not enable HTTP
- tests proving safe summaries do not expose secrets or raw provider payloads

## Success sanitizer contract

Allowed future response fields:

- id
- name
- cpfCnpj
- email
- mobilePhone

Blocked future response fields:

- access_token
- api_key
- webhook_token
- wallet_id
- headers
- raw
- provider_raw

The contract keeps:

- raw_response_allowed: false
- secret_values_allowed: false
- safe_fields_only: true

## Error sanitizer contract

Allowed future error fields:

- status_code
- provider_error_code
- safe_message
- retryable

Blocked future error fields:

- access_token
- api_key
- webhook_token
- wallet_id
- headers
- raw
- provider_raw
- stacktrace

The contract keeps:

- raw_error_allowed: false
- secret_values_allowed: false
- safe_fields_only: true

## Manual authorization

The mandatory phrase may be recognized:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

Even when the phrase is recognized, the sanitizer contract cannot send HTTP.

Manual authorization registered does not enable the adapter.

## Blocked state

The sanitizer contract keeps:

- sanitizer_contract_defined: true
- sanitizer_implemented: false
- raw_response_retained: false
- raw_error_retained: false
- sandbox_only: true
- adapter_implemented: false
- adapter_enabled: false
- can_send_http: false
- network_call_allowed: false
- real_money: false
- http_call_executed: false
- ready_for_http_execution: false

## Explicit non-goals

This milestone does not:

- import requests;
- import httpx;
- import aiohttp;
- import urllib;
- implement a network adapter;
- open a network connection;
- execute HTTP;
- send a request to Asaas;
- create a real customer;
- create a Pix charge;
- retrieve a Pix QR Code;
- check real payment status;
- use production;
- move real money;
- expose API Key;
- expose access_token value;
- expose webhook token;
- expose Wallet ID;
- expose raw response;
- expose raw provider error;
- expose headers;
- expose stacktrace.

## Validation

Validation command:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Expected result:

40 passed

## Decision

The project now has a response sanitizer contract for the future first Asaas Sandbox POST /customers call.

The adapter is still not implemented, not enabled and cannot send HTTP.

## Next likely milestone

v0.2.56-wallet-asaas-sandbox-first-customer-http-error-sanitizer-contract
