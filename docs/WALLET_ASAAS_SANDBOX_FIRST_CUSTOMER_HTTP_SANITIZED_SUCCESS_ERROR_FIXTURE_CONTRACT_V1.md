# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Sanitized Success Error Fixture Contract V1

Milestone: `v0.2.66-wallet-asaas-sandbox-first-customer-http-sanitized-success-error-fixture-contract`

## Purpose

This milestone adds sanitized success and error fixtures for the future first Asaas Sandbox `POST /customers` HTTP call.

The fixtures are contract-only examples. They define the safe shape expected from future sanitized success and sanitized error handling without exposing raw Asaas provider payloads, raw provider errors, request body or stacktraces.

## Scope

The sanitized success/error fixture contract is built on top of:

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

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/customers`
- Operation: `create_customer`
- Authentication model: `access_token` header, never exposed in safe summaries

## Sanitized fixture contract

The contract records:

- `target_method`: `POST`
- `target_path`: `/customers`
- `target_environment`: `sandbox`
- `requires_sanitized_result_envelope_contract`: `true`
- `requires_success_fixture`: `true`
- `requires_error_fixture`: `true`
- `fixtures_are_sanitized`: `true`
- `success_fixture_contains_raw_provider_payload`: `false`
- `error_fixture_contains_raw_provider_error`: `false`
- `request_body_exposure_allowed`: `false`
- `stacktrace_exposure_allowed`: `false`
- `current_fixtures_are_contract_only`: `true`

## Sanitized success fixture

The success fixture uses only safe fields:

- `ok`: `true`
- `operation`: `create_customer`
- `provider`: `asaas`
- `environment`: `sandbox`
- `asaas_customer_id_present`: `true`
- `http_status_class`: `2xx`
- `sanitized_customer_reference`: `asaas_customer_sandbox_fixture_redacted`
- `raw_provider_payload_included`: `false`

## Sanitized error fixture

The error fixture uses only safe fields:

- `ok`: `false`
- `operation`: `create_customer`
- `provider`: `asaas`
- `environment`: `sandbox`
- `error_category`: `provider_rejected_or_unavailable`
- `retryable`: `false`
- `http_status_class`: `4xx_or_5xx`
- `raw_provider_error_included`: `false`
- `stacktrace_included`: `false`

## Safety state

Even when the full previous gate chain is valid, this milestone keeps:

- `sanitized_result_envelope_contract_valid`: `true`
- `sanitized_success_fixture_defined`: `true`
- `sanitized_error_fixture_defined`: `true`
- `sanitized_fixtures_match_envelope_contract`: `true`
- `success_fixture_contains_raw_provider_payload`: `false`
- `error_fixture_contains_raw_provider_error`: `false`
- `request_body_exposure_allowed`: `false`
- `stacktrace_exposure_allowed`: `false`
- `fixture_contract_allows_adapter_enablement`: `false`
- `fixture_contract_allows_http_execution`: `false`
- `fixture_contract_can_include_raw_payload`: `false`
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

`67 passed`

## Next likely milestone

`v0.2.67-wallet-asaas-sandbox-first-customer-http-adapter-boundary-final-contract`
