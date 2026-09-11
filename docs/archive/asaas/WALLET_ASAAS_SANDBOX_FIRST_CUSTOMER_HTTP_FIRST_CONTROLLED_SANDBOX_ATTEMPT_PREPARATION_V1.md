# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP First Controlled Sandbox Attempt Preparation V1

Milestone: `v0.2.69-wallet-asaas-sandbox-first-customer-http-first-controlled-sandbox-attempt-preparation`

## Purpose

This milestone adds the preparation contract for the future first controlled Asaas Sandbox `POST /customers` HTTP attempt.

The preparation is non-executing. It confirms that the first controlled Sandbox attempt must only happen after manual operator review, with Sandbox-only configuration, environment-loaded secrets, sanitized envelopes, redacted logs and a single-attempt policy.

This milestone does not execute HTTP.

## Scope

The first controlled Sandbox attempt preparation is built on top of:

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
- the adapter boundary final contract
- the final manual execution runbook readiness gate

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/customers`
- Operation: `create_customer`
- Authentication model: `access_token` header, never exposed in safe summaries

## First controlled Sandbox attempt preparation

The preparation records:

- `target_method`: `POST`
- `target_path`: `/customers`
- `target_environment`: `sandbox`
- `requires_final_manual_execution_runbook_readiness_gate`: `true`
- `requires_manual_operator_review`: `true`
- `requires_sandbox_base_url_confirmation`: `true`
- `requires_environment_secret_loading_only`: `true`
- `requires_no_production_credentials`: `true`
- `requires_no_real_money_or_real_pix_flow`: `true`
- `requires_sanitized_success_envelope`: `true`
- `requires_sanitized_error_envelope`: `true`
- `requires_redacted_logs_only`: `true`
- `requires_single_controlled_attempt_policy`: `true`
- `requires_no_retry_loop`: `true`
- `requires_manual_stop_on_unexpected_response`: `true`
- `requires_no_raw_provider_payload_storage`: `true`
- `requires_no_request_body_logging`: `true`
- `requires_no_stacktrace_exposure`: `true`
- `first_controlled_attempt_not_executed`: `true`
- `current_preparation_is_non_executing`: `true`

## First controlled attempt checklist

Before any real Sandbox HTTP attempt, the operator must confirm:

- `confirm_main_branch_clean_and_tagged`
- `confirm_sandbox_environment_variables_exist_locally`
- `confirm_no_production_base_url_or_credentials`
- `confirm_manual_operator_is_present`
- `confirm_single_attempt_only`
- `confirm_sanitized_logging_only`
- `confirm_no_request_body_logging`
- `confirm_no_raw_provider_payload_storage`
- `confirm_stop_on_unexpected_response`
- `confirm_post_attempt_sanitized_record_required`

## Safety state

Even when the full previous gate chain is valid, this milestone keeps:

- `final_manual_execution_runbook_readiness_gate_valid`: `true`
- `first_controlled_sandbox_attempt_preparation_valid`: `true`
- `ready_for_first_controlled_sandbox_attempt_review`: `true`
- `manual_operator_review_required`: `true`
- `sandbox_base_url_confirmation_required`: `true`
- `environment_secret_loading_only_required`: `true`
- `no_production_credentials_required`: `true`
- `no_real_money_or_real_pix_flow_required`: `true`
- `sanitized_success_envelope_required`: `true`
- `sanitized_error_envelope_required`: `true`
- `redacted_logs_only_required`: `true`
- `single_controlled_attempt_policy_required`: `true`
- `no_retry_loop_required`: `true`
- `manual_stop_on_unexpected_response_required`: `true`
- `raw_provider_payload_storage_allowed`: `false`
- `request_body_logging_allowed`: `false`
- `stacktrace_exposure_allowed`: `false`
- `first_controlled_attempt_allows_adapter_implementation`: `false`
- `first_controlled_attempt_allows_adapter_enablement`: `false`
- `first_controlled_attempt_allows_http_execution`: `false`
- `first_controlled_attempt_can_emit_raw_payload`: `false`
- `first_controlled_attempt_executed`: `false`
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

`76 passed`

## Next likely milestone

`v0.2.70-wallet-asaas-sandbox-first-customer-http-operator-decision-gate`
