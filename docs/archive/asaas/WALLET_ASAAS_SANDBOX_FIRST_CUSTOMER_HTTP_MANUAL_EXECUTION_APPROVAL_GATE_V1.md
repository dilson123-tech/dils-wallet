# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Manual Execution Approval Gate V1

Milestone: v0.2.58-wallet-asaas-sandbox-first-customer-http-manual-execution-approval-gate

## Purpose

This milestone adds a manual execution approval gate for the future first Asaas Sandbox POST /customers HTTP call.

The gate can recognize the mandatory manual authorization phrase, but it still does not allow HTTP execution.

This milestone still does not implement a real HTTP adapter and does not send any request to Asaas.

## Confirmed Asaas target

The future target remains:

- Base URL: https://sandbox.asaas.com/api/v3
- Method: POST
- Path: /customers
- Operation: create_customer
- Authentication header name: access_token
- Environment: sandbox

## What changed

Added:

- AsaasFirstCustomerHttpManualExecutionApprovalGateResult
- gate_first_customer_http_manual_execution_approval
- manual execution approval checklist
- tests proving the gate remains blocked without manual authorization
- tests proving the gate recognizes manual authorization but still does not enable HTTP

## Approval checklist

The gate records the following safety checklist:

- sandbox_target_confirmed: true
- production_blocked: true
- real_money_disabled: true
- safe_response_sanitizer_required: true
- safe_error_sanitizer_required: true
- raw_response_exposure_blocked: true
- raw_error_exposure_blocked: true
- request_body_exposure_blocked: true
- stacktrace_exposure_blocked: true
- secret_exposure_blocked: true
- adapter_implementation_reviewed: false
- final_operator_confirmation_required: true

## Manual authorization phrase

The mandatory phrase remains:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

When the phrase is missing:

- manual_execution_approval_registered: false
- manual_execution_approval_valid: false

When the phrase is present:

- manual_execution_approval_registered: true
- manual_execution_approval_valid: true

Even when valid, the gate keeps:

- approval_allows_http_execution: false
- execution_enabled: false
- can_send_http: false
- network_call_allowed: false
- http_call_executed: false
- ready_for_http_execution: false

## Blocked state

The manual execution approval gate keeps:

- approval_gate_defined: true
- approval_allows_http_execution: false
- execution_enabled: false
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
- expose raw response;
- expose raw error;
- expose raw provider error;
- expose stacktrace.

## Validation

Validation command:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Expected result:

44 passed

## Decision

The project now has a manual execution approval gate for the future first Asaas Sandbox POST /customers call.

The adapter is still not implemented, not enabled and cannot send HTTP.

## Next likely milestone

v0.2.59-wallet-asaas-sandbox-first-customer-http-disabled-adapter-shell
