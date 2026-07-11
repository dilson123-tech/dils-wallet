# Aurea Gold Wallet — Asaas Sandbox Subaccount First Controlled Attempt Evidence Template V1

Milestone: `v0.2.88-wallet-asaas-sandbox-subaccount-first-controlled-attempt-evidence-template-v1`

## Purpose

This milestone adds the sanitized evidence template for a future first controlled Asaas Sandbox subaccount attempt.

The template defines what may be recorded after a future Sandbox-only `POST /accounts` attempt and what must never be recorded.

This milestone does not execute HTTP.

## Scope

The evidence template is built on top of:

- `v0.2.85-wallet-asaas-sandbox-subaccount-first-controlled-attempt-runbook-v1`
- `v0.2.86-wallet-asaas-sandbox-subaccount-first-controlled-attempt-preflight-v1`
- `v0.2.87-wallet-asaas-sandbox-subaccount-first-controlled-attempt-operator-review-v1`

The template is documentation-only. It does not add an HTTP adapter, enable network execution, call Asaas, create a subaccount, expose secrets or move money.

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/accounts`
- Operation: `create_subaccount`
- Authentication model: environment-loaded `access_token` only
- Payload policy: no raw payload storage
- Response policy: sanitized response fields only
- Attempt policy: single controlled attempt only in a future milestone
- Retry policy: no retry loop
- Stop policy: manual stop on unexpected response

## Evidence record status

The current evidence template status is:

- `evidence_template_defined`: `true`
- `evidence_record_created`: `false`
- `first_controlled_subaccount_attempt_executed`: `false`
- `subaccount_creation_executed`: `false`
- `operator_approval_to_execute_http`: `false`
- `can_create_subaccount`: `false`
- `can_send_http`: `false`
- `network_call_allowed`: `false`
- `real_money`: `false`
- `http_call_executed`: `false`
- `ready_for_http_execution`: `false`

This milestone defines the evidence shape only. It does not approve or perform the future attempt.

## Sanitized evidence template

A future sanitized evidence record must use this shape:

- `milestone`: future controlled attempt milestone
- `operation`: `asaas_sandbox_subaccount_first_controlled_attempt`
- `environment`: `sandbox`
- `target_method`: `POST`
- `target_path`: `/accounts`
- `request_executed`: boolean
- `http_call_executed`: boolean
- `http_status_code`: sanitized status code or `null`
- `subaccount_created`: boolean
- `object`: sanitized object type or `null`
- `api_key_present`: boolean only
- `wallet_id_present`: boolean only
- `account_id_present`: boolean only
- `onboarding_url_present`: boolean only
- `sensitive_response_values_masked`: boolean
- `raw_payload_stored`: `false`
- `raw_response_stored`: `false`
- `raw_error_stored`: `false`
- `raw_headers_stored`: `false`
- `request_body_logged`: `false`
- `response_body_logged`: `false`
- `production_used`: `false`
- `real_money`: `false`
- `retry_loop_used`: `false`
- `manual_stop_required`: boolean
- `unexpected_response_detected`: boolean
- `next_step_required`: manual review marker

The template intentionally uses booleans, status indicators and null placeholders instead of real provider identifiers.

## Required sanitized fields

A future record may include only:

- `milestone`
- `operation`
- `environment`
- `target_method`
- `target_path`
- `request_executed`
- `http_call_executed`
- `http_status_code`
- `subaccount_created`
- `object`
- `api_key_present`
- `wallet_id_present`
- `account_id_present`
- `onboarding_url_present`
- `sensitive_response_values_masked`
- `raw_payload_stored`
- `raw_response_stored`
- `raw_error_stored`
- `raw_headers_stored`
- `request_body_logged`
- `response_body_logged`
- `production_used`
- `real_money`
- `retry_loop_used`
- `manual_stop_required`
- `unexpected_response_detected`
- `next_step_required`

## Forbidden evidence values

A future evidence record must never include:

- access token
- API key value
- webhook token value
- `.env` content
- raw request body
- raw response body
- raw error body
- raw headers
- `walletId` value
- `id` value
- `onboardingUrl` value
- real customer identifier
- real payment identifier
- real event identifier
- production credential
- production URL
- screenshot containing credentials

## Sanitization rules

The future evidence writer must follow these rules:

1. Convert provider identifiers to booleans

   - `apiKey` becomes `api_key_present`
   - `walletId` becomes `wallet_id_present`
   - `id` becomes `account_id_present`
   - `onboardingUrl` becomes `onboarding_url_present`

2. Never persist raw provider data

   - raw payload storage remains blocked
   - raw response storage remains blocked
   - raw error storage remains blocked
   - raw header storage remains blocked

3. Never log sensitive bodies

   - request body logging remains blocked
   - response body logging remains blocked
   - error body logging remains blocked
   - stacktrace exposure remains blocked

4. Preserve execution safety state

   - production remains blocked
   - real money remains blocked
   - retry loop remains blocked
   - unexpected response requires manual stop

## Example sanitized success evidence

A future successful Sandbox attempt may be summarized with:

- `request_executed`: `true`
- `http_call_executed`: `true`
- `http_status_code`: `200`
- `subaccount_created`: `true`
- `object`: `account`
- `api_key_present`: `true`
- `wallet_id_present`: `true`
- `account_id_present`: `true`
- `onboarding_url_present`: `true`
- `sensitive_response_values_masked`: `true`
- `raw_payload_stored`: `false`
- `raw_response_stored`: `false`
- `production_used`: `false`
- `real_money`: `false`
- `retry_loop_used`: `false`

This is an example shape only. It is not evidence that any request has been executed.

## Example sanitized error evidence

A future failed Sandbox attempt may be summarized with:

- `request_executed`: `true`
- `http_call_executed`: `true`
- `http_status_code`: sanitized error status code
- `subaccount_created`: `false`
- `object`: `null`
- `api_key_present`: `false`
- `wallet_id_present`: `false`
- `account_id_present`: `false`
- `onboarding_url_present`: `false`
- `sensitive_response_values_masked`: `true`
- `raw_payload_stored`: `false`
- `raw_response_stored`: `false`
- `raw_error_stored`: `false`
- `raw_headers_stored`: `false`
- `production_used`: `false`
- `real_money`: `false`
- `retry_loop_used`: `false`
- `manual_stop_required`: `true`
- `unexpected_response_detected`: `true`

This is an example shape only. It must not include the raw provider error body.

## Operator evidence review checklist

Before any future evidence record is accepted, the operator must confirm:

- `confirm_evidence_uses_template`
- `confirm_environment_is_sandbox`
- `confirm_target_method_is_post`
- `confirm_target_path_is_accounts`
- `confirm_no_access_token_exposed`
- `confirm_no_api_key_value_exposed`
- `confirm_no_webhook_token_value_exposed`
- `confirm_no_env_content_exposed`
- `confirm_no_raw_payload_stored`
- `confirm_no_raw_response_stored`
- `confirm_no_raw_error_stored`
- `confirm_no_raw_headers_stored`
- `confirm_no_request_body_logged`
- `confirm_no_response_body_logged`
- `confirm_no_wallet_id_value_exposed`
- `confirm_no_account_id_value_exposed`
- `confirm_no_onboarding_url_value_exposed`
- `confirm_sensitive_response_values_masked`
- `confirm_production_not_used`
- `confirm_real_money_false`
- `confirm_retry_loop_not_used`
- `confirm_manual_stop_policy_respected`

## Safety state

This milestone keeps:

- `evidence_template_defined`: `true`
- `evidence_record_created`: `false`
- `first_controlled_subaccount_attempt_executed`: `false`
- `subaccount_creation_executed`: `false`
- `operator_approval_to_execute_http`: `false`
- `manual_operator_review_required`: `true`
- `first_controlled_attempt_preflight_required`: `true`
- `sanitized_evidence_required`: `true`
- `sandbox_base_url_confirmation_required`: `true`
- `environment_secret_loading_only_required`: `true`
- `no_production_credentials_required`: `true`
- `payload_builder_guard_required`: `true`
- `response_sanitizer_required`: `true`
- `redacted_logs_only_required`: `true`
- `single_controlled_attempt_policy_required`: `true`
- `no_retry_loop_required`: `true`
- `manual_stop_on_unexpected_response_required`: `true`
- `raw_payload_storage_allowed`: `false`
- `raw_response_storage_allowed`: `false`
- `raw_error_storage_allowed`: `false`
- `raw_headers_storage_allowed`: `false`
- `request_body_logging_allowed`: `false`
- `response_body_logging_allowed`: `false`
- `can_create_subaccount`: `false`
- `can_send_http`: `false`
- `network_call_allowed`: `false`
- `real_money`: `false`
- `http_call_executed`: `false`
- `ready_for_http_execution`: `false`

## Non-goals

This milestone does not implement an HTTP adapter, enable a network binding, define a send method, execute an Asaas request, create an Asaas subaccount, recover a real `onboardingUrl`, configure split, create a charge, generate a QR Code, receive a real payment, reconcile balances, test rate limits, test error cases, use production, move real money, expose secrets, expose raw payloads, expose raw responses, expose raw errors, expose raw headers or expose stacktraces.

## Validation

Expected validation command:

`git diff --check`

No Python test count is expected to change in this documentation-only milestone.

## Next likely milestone

`v0.2.89-wallet-asaas-sandbox-subaccount-first-controlled-attempt-record-contract-v1`
