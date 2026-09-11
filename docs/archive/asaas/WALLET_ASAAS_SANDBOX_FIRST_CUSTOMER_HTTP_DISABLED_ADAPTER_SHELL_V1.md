# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Disabled Adapter Shell V1

Milestone: `v0.2.59-wallet-asaas-sandbox-first-customer-http-disabled-adapter-shell`

## Purpose

This milestone adds the disabled adapter shell for the future first Asaas Sandbox `POST /customers` HTTP call.

The shell exists only as a safe architecture boundary. It does not select an HTTP client library, does not create a network binding, does not define a send method, does not define an execution method and does not perform any HTTP call.

## Scope

The disabled adapter shell is built on top of the previous manual execution approval gate.

A valid manual authorization phrase may be recognized by the previous gate, but this milestone still keeps HTTP execution blocked.

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/customers`
- Operation: `create_customer`
- Authentication model: `access_token` header, never exposed in safe summaries

## Added behavior

The new shell records the following safe contract:

- `target_method`: `POST`
- `target_path`: `/customers`
- `target_environment`: `sandbox`
- `http_client_library_selected`: `false`
- `network_binding_created`: `false`
- `send_method_defined`: `false`
- `execution_method_defined`: `false`
- `requires_future_explicit_enablement`: `true`

## Safety state

The disabled adapter shell keeps:

- `disabled_adapter_shell_defined`: `true`
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

This milestone does not implement an HTTP adapter, select an HTTP client library, create a network binding, define a send method, define an execution method, execute an Asaas request, create an Asaas customer, create a Pix payment, fetch a Pix QR Code, fetch a payment status, use production, move real money, expose secrets, expose raw provider payloads, expose request body or expose stacktrace.

## Validation

Expected validation command:

`pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q`

Expected result:

`46 passed`

## Next likely milestone

`v0.2.60-wallet-asaas-sandbox-first-customer-http-explicit-enable-preflight`
