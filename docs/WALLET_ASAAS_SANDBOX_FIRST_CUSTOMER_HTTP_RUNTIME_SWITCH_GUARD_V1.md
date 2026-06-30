# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Runtime Switch Guard V1

Milestone: `v0.2.62-wallet-asaas-sandbox-first-customer-http-runtime-switch-guard`

## Purpose

This milestone adds the runtime switch guard for the future first Asaas Sandbox `POST /customers` HTTP call.

The guard is a non-executing safety boundary. It can recognize the required runtime switch phrase and validate the previous runtime enable contract, but it does not enable the adapter, does not enable HTTP execution and does not execute any Asaas request.

## Scope

The runtime switch guard is built on top of:

- the prepared Sandbox customer request
- the response sanitizer contract
- the error sanitizer contract
- the pre-execution safety review
- the manual execution approval gate
- the disabled adapter shell
- the explicit enable preflight
- the runtime enable contract

## Required runtime switch phrase

`CONFIRMO GUARD DO SWITCH RUNTIME ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.`

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/customers`
- Operation: `create_customer`
- Authentication model: `access_token` header, never exposed in safe summaries

## Runtime switch guard contract

The guard records:

- `target_method`: `POST`
- `target_path`: `/customers`
- `target_environment`: `sandbox`
- `requires_manual_execution_approval`: `true`
- `requires_disabled_adapter_shell`: `true`
- `requires_explicit_enable_preflight`: `true`
- `requires_runtime_enable_contract`: `true`
- `requires_runtime_switch_phrase`: `true`
- `runtime_switch_default_state`: `disabled`
- `requires_future_http_adapter_implementation`: `true`
- `requires_future_runtime_execution_gate`: `true`
- `current_guard_is_non_executing`: `true`

## Safety state

Even when the manual authorization phrase, explicit enable phrase, runtime enable phrase and runtime switch phrase are all valid, this milestone keeps:

- `runtime_switch_guard_valid`: `true`
- `runtime_switch_requested`: `true`
- `runtime_switch_allows_adapter_enablement`: `false`
- `runtime_switch_allows_http_execution`: `false`
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

`55 passed`

## Next likely milestone

`v0.2.63-wallet-asaas-sandbox-first-customer-http-execution-gate-contract`
