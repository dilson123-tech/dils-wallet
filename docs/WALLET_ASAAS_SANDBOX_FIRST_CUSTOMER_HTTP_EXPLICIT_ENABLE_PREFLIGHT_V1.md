# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Explicit Enable Preflight V1

Milestone: `v0.2.60-wallet-asaas-sandbox-first-customer-http-explicit-enable-preflight`

## Purpose

This milestone adds the explicit enable preflight for the future first Asaas Sandbox `POST /customers` HTTP call.

The preflight is a non-executing safety gate. It can recognize the required explicit enable phrase, but it does not enable the adapter, does not enable HTTP execution and does not execute any Asaas request.

## Scope

The explicit enable preflight is built on top of:

- the prepared Sandbox customer request
- the response sanitizer contract
- the error sanitizer contract
- the pre-execution safety review
- the manual execution approval gate
- the disabled adapter shell

## Required explicit enable phrase

`CONFIRMO PREFLIGHT DE HABILITACAO EXPLICITA ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.`

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/customers`
- Operation: `create_customer`
- Authentication model: `access_token` header, never exposed in safe summaries

## Preflight contract

The preflight records:

- `target_method`: `POST`
- `target_path`: `/customers`
- `target_environment`: `sandbox`
- `requires_manual_execution_approval`: `true`
- `requires_disabled_adapter_shell`: `true`
- `requires_explicit_enable_phrase`: `true`
- `requires_future_http_adapter_implementation`: `true`
- `requires_future_runtime_enablement`: `true`
- `current_preflight_is_non_executing`: `true`

## Safety state

Even when the manual authorization phrase and the explicit enable phrase are both valid, this milestone keeps:

- `explicit_enable_preflight_valid`: `true`
- `explicit_enable_allows_adapter_enablement`: `false`
- `explicit_enable_allows_http_execution`: `false`
- `adapter_shell_enabled`: `false`
- `adapter_implemented`: `false`
- `adapter_enabled`: `false`
- `execution_enabled`: `false`
- `can_send_http`: `false`
- `network_call_allowed`: `false`
- `real_money`: `false`
- `http_call_executed`: `false`
- `ready_for_http_execution`: `false`

## Non-goals

This milestone does not import or use any HTTP client library.

This milestone does not implement an HTTP adapter, enable the disabled adapter shell, create a network binding, define a send method, define an execution method, execute an Asaas request, create an Asaas customer, create a Pix payment, fetch a Pix QR Code, fetch a payment status, use production, move real money, expose secrets, expose raw provider payloads, expose request body or expose stacktrace.

## Validation

Expected validation command:

`pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q`

Expected result:

`49 passed`

## Next likely milestone

`v0.2.61-wallet-asaas-sandbox-first-customer-http-runtime-enable-contract`
