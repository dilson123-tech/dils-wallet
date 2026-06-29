# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Error Sanitizer Contract V1

Milestone: v0.2.56-wallet-asaas-sandbox-first-customer-http-error-sanitizer-contract

## Purpose

This milestone adds a dedicated error sanitizer contract for the future first Asaas Sandbox POST /customers HTTP call.

The contract defines a safe error shape for future provider errors while blocking secrets, raw provider payloads, stacktraces, headers and request bodies.

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

- AsaasFirstCustomerHttpErrorSanitizerContractResult
- build_first_customer_http_error_sanitizer_contract
- dedicated safe error shape
- safe error categories
- tests proving the error sanitizer contract remains blocked
- tests proving manual authorization does not enable HTTP
- tests proving safe summaries do not expose secrets

## Safe error shape

Allowed future error fields:

- status_code
- provider_error_code
- safe_message
- retryable
- category

Blocked future error fields:

- access_token
- api_key
- webhook_token
- wallet_id
- headers
- raw
- provider_raw
- stacktrace
- request_body

The contract keeps:

- raw_error_allowed: false
- provider_raw_error_allowed: false
- stacktrace_allowed: false
- secret_values_allowed: false
- safe_fields_only: true

## Safe error categories

The future adapter may classify sanitized provider errors into:

- provider_validation_error
- provider_authentication_error
- provider_rate_limit_error
- provider_unavailable
- unexpected_provider_error

These categories are only a contract in this milestone. No HTTP call is executed.

## Manual authorization

The mandatory phrase may be recognized:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

Even when the phrase is recognized, the error sanitizer contract cannot send HTTP.

Manual authorization registered does not enable the adapter.

## Blocked state

The error sanitizer contract keeps:

- error_sanitizer_contract_defined: true
- error_sanitizer_implemented: false
- raw_error_retained: false
- provider_raw_error_retained: false
- stacktrace_retained: false
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
- expose headers;
- expose request body;
- expose raw error;
- expose raw provider error;
- expose stacktrace.

## Validation

Validation command:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Expected result:

42 passed

## Decision

The project now has a dedicated error sanitizer contract for the future first Asaas Sandbox POST /customers call.

The adapter is still not implemented, not enabled and cannot send HTTP.

## Next likely milestone

v0.2.57-wallet-asaas-sandbox-first-customer-http-pre-execution-safety-review
