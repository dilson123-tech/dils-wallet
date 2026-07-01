# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Sanitized Execution Handler Contract V1

Milestone: `v0.2.64-wallet-asaas-sandbox-first-customer-http-sanitized-execution-handler-contract`

## Purpose

This milestone adds the sanitized execution handler contract for the future first Asaas Sandbox `POST /customers` HTTP call.

The contract is a non-executing safety boundary. It validates the previous execution gate contract and defines that any future execution path must use sanitized response and sanitized error handling only.

## Scope

The sanitized execution handler contract is built on top of:

- the prepared Sandbox customer request
- the response sanitizer contract
- the error sanitizer contract
- the pre-execution safety review
- the manual execution approval gate
- the disabled adapter shell
- the explicit enable preflight
- the runtime enable contract
- the runtime switch guard
- the execution gate contract

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/customers`
- Operation: `create_customer`
- Authentication model: `access_token` header, never exposed in safe summaries

## Sanitized execution handler contract

The contract records:

- `target_method`: `POST`
- `target_path`: `/customers`
- `target_environment`: `sandbox`
- `requires_execution_gate_contract`: `true`
- `requires_future_http_adapter_implementation`: `true`
- `requires_sanitized_response_handler`: `true`
- `requires_sanitized_error_handler`: `true`
- `raw_provider_response_allowed`: `false`
- `raw_provider_error_allowed`: `false`
- `request_body_exposure_allowed`: `false`
- `stacktrace_exposure_allowed`: `false`
- `current_handler_is_non_executing`: `true`

## Safety state

Even when the execution gate contract is valid, this milestone keeps:

- `execution_gate_contract_valid`: `true`
- `sanitized_response_handler_required`: `true`
- `sanitized_error_handler_required`: `true`
- `raw_provider_response_allowed`: `false`
- `raw_provider_error_allowed`: `false`
- `request_body_exposure_allowed`: `false`
- `stacktrace_exposure_allowed`: `false`
- `sanitized_handler_allows_adapter_enablement`: `false`
- `sanitized_handler_allows_http_execution`: `false`
- `sanitized_handler_can_process_raw_provider_payload`: `false`
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

This milestone does not implement an HTTP adapter, enable the disabled adapter shell, create a network binding, define a send method, define an execution method, execute an Asaas request, create an Asaas customer, create a Pix payment, fetch a Pix QR Code, fetch a payment status, use production, move real money, expose secrets, expose raw provider response, expose raw provider error, expose request body or expose stacktrace.

## Validation

Expected validation command:

`pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q`

Expected result:

`61 passed`

## Next likely milestone

`v0.2.65-wallet-asaas-sandbox-first-customer-http-sanitized-result-envelope-contract`
