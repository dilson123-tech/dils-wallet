# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Adapter Boundary Final Contract V1

Milestone: `v0.2.67-wallet-asaas-sandbox-first-customer-http-adapter-boundary-final-contract`

## Purpose

This milestone adds the final adapter boundary contract for the future first Asaas Sandbox `POST /customers` HTTP call.

The contract is a non-executing safety boundary. It defines which internal caller may use the future adapter and which gates, sanitized handlers, sanitized envelopes and sanitized fixtures must be valid before any future HTTP adapter implementation can be considered.

## Scope

The adapter boundary final contract is built on top of:

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
- the sanitized execution handler contract
- the sanitized result envelope contract
- the sanitized success/error fixture contract

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/customers`
- Operation: `create_customer`
- Authentication model: `access_token` header, never exposed in safe summaries

## Adapter boundary final contract

The contract records:

- `target_method`: `POST`
- `target_path`: `/customers`
- `target_environment`: `sandbox`
- `allowed_future_caller`: `first_customer_http_sanitized_execution_handler`
- `requires_manual_execution_approval`: `true`
- `requires_disabled_adapter_shell`: `true`
- `requires_explicit_enable_preflight`: `true`
- `requires_runtime_enable_contract`: `true`
- `requires_runtime_switch_guard`: `true`
- `requires_execution_gate_contract`: `true`
- `requires_sanitized_execution_handler_contract`: `true`
- `requires_sanitized_result_envelope_contract`: `true`
- `requires_sanitized_success_error_fixtures`: `true`
- `future_adapter_must_return_sanitized_envelope_only`: `true`
- `future_adapter_must_not_expose_raw_provider_payload`: `true`
- `future_adapter_must_not_expose_raw_provider_error`: `true`
- `future_adapter_must_not_expose_request_body`: `true`
- `future_adapter_must_not_expose_stacktrace`: `true`
- `adapter_implementation_present`: `false`
- `current_boundary_is_contract_only`: `true`

## Safety state

Even when the full previous gate chain is valid, this milestone keeps:

- `sanitized_success_error_fixture_contract_valid`: `true`
- `adapter_boundary_final_contract_valid`: `true`
- `future_adapter_must_return_sanitized_envelope_only`: `true`
- `raw_provider_payload_allowed`: `false`
- `raw_provider_error_allowed`: `false`
- `request_body_exposure_allowed`: `false`
- `stacktrace_exposure_allowed`: `false`
- `adapter_boundary_allows_adapter_implementation`: `false`
- `adapter_boundary_allows_adapter_enablement`: `false`
- `adapter_boundary_allows_http_execution`: `false`
- `adapter_boundary_can_emit_raw_payload`: `false`
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

`70 passed`

## Next likely milestone

`v0.2.68-wallet-asaas-sandbox-first-customer-http-final-manual-execution-runbook-readiness-gate`
