# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Blocked Adapter Contract V1

Milestone: v0.2.54-wallet-asaas-sandbox-first-customer-http-blocked-adapter-contract

## Purpose

This milestone adds a blocked contract for the future Asaas Sandbox first customer HTTP adapter.

The contract defines the expected request, safe response shape and sanitized error shape for the future POST /customers call.

This milestone still does not implement a real HTTP adapter and does not send any request to Asaas.

## Confirmed Asaas target

The target remains based on the Asaas Sandbox guidance:

- Base URL: https://sandbox.asaas.com/api/v3
- Method: POST
- Path: /customers
- Operation: create_customer
- Authentication header name: access_token
- Environment: sandbox

## What changed

Added:

- AsaasFirstCustomerHttpBlockedAdapterContractResult
- build_first_customer_http_blocked_adapter_contract
- request contract for the future POST /customers adapter
- safe response contract
- sanitized error contract
- tests proving the contract remains blocked
- tests proving manual authorization does not enable HTTP
- tests proving the safe summary does not expose secrets

## Request contract

The request contract defines:

- method: POST
- path: /customers
- operation: create_customer
- required header names: access_token
- sensitive header values masked: true
- required JSON fields:
  - name
  - cpfCnpj
  - email
  - mobilePhone

## Response contract

The response contract defines:

- expected success statuses:
  - 200
  - 201
- expected safe fields:
  - id
  - name
  - cpfCnpj
  - email
  - mobilePhone
- raw response blocked: true
- secret values allowed: false

## Error contract

The error contract defines only sanitized fields:

- status_code
- provider_error_code
- safe_message
- retryable

The raw provider error remains blocked.

Secret values are not allowed in errors.

## Manual authorization

The mandatory phrase may be recognized:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

Even when the phrase is recognized, the contract cannot send HTTP.

Manual authorization registered does not enable the adapter.

## Blocked adapter state

The contract keeps:

- sandbox_only: true
- target_allowed: true for POST /customers create_customer
- adapter_implemented: false
- adapter_enabled: false
- can_send_http: false
- network_call_allowed: false
- retry_enabled: false
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
- expose raw provider error.

## Validation

Validation command:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Expected result:

38 passed

## Decision

The project now has a blocked adapter contract for the future first Asaas Sandbox POST /customers call.

The adapter is still not implemented, not enabled and cannot send HTTP.

## Next likely milestone

v0.2.55-wallet-asaas-sandbox-first-customer-http-response-sanitizer-contract
