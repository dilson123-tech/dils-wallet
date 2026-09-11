# Aurea Gold Wallet — Asaas Sandbox Subaccount First Controlled Attempt Runbook V1

Milestone: `v0.2.85-wallet-asaas-sandbox-subaccount-first-controlled-attempt-runbook-v1`

## Purpose

This milestone adds the non-executing runbook for the future first controlled Asaas Sandbox subaccount attempt.

The runbook prepares the operator checklist for a future Sandbox-only `POST /accounts` attempt, after the subaccount payload contract, payload builder guard, sanitized fixture, response sanitizer contract, response sanitizer implementation and manual execution gate are already in place.

This milestone does not execute HTTP.

## Scope

The first controlled subaccount attempt runbook is built on top of:

- `v0.2.78-wallet-asaas-sandbox-subaccount-structure-guard-v1`
- `v0.2.79-wallet-asaas-sandbox-subaccount-payload-contract-v1`
- `v0.2.80-wallet-asaas-sandbox-subaccount-payload-builder-guard-v1`
- `v0.2.81-wallet-asaas-sandbox-subaccount-sanitized-fixture-v1`
- `v0.2.82-wallet-asaas-sandbox-subaccount-response-sanitizer-contract-v1`
- `v0.2.83-wallet-asaas-sandbox-subaccount-response-sanitizer-implementation-v1`
- `v0.2.84-wallet-asaas-sandbox-subaccount-manual-execution-gate-v1`

## Target Asaas operation

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/accounts`
- Operation: `create_subaccount`
- Authentication model: `access_token` header, never exposed in docs, logs, summaries or chat
- Payload policy: sanitized local review only before any future attempt
- Response policy: sanitized output only, no raw response storage

## Asaas validation expectations covered by this runbook

The current Asaas validation path requires future evidence for:

- creating test subaccounts
- validating permissions
- validating `onboardingUrl` recovery if applicable to the operating model
- validating returned data structure
- configuring and testing split if the operation uses split
- simulating a charge split between accounts
- validating each split part routing
- validating reconciliation with `GET /v3/accounts/me/income`
- comparing income records with `PAYMENT_RECEIVED` webhooks
- checking balances, period filters and status filters
- reviewing rate limits and quotas before production
- validating expected errors such as invalid CPF/CNPJ, duplicated customer, expired charge, malformed request and webhook endpoint outage/retry behavior
- documenting safe error codes
- validating the end-to-end Sandbox flow: customer, charge, QR Code, webhook payment event and wallet statement

This milestone only prepares the first controlled subaccount attempt. Split, reconciliation, rate limits, error validation and end-to-end evidence remain future milestones.

## Preconditions before any future controlled attempt

The operator must confirm:

- `confirm_main_branch_clean_and_tagged`
- `confirm_latest_tag_is_v0_2_85_or_later`
- `confirm_sandbox_environment_only`
- `confirm_no_production_base_url`
- `confirm_no_production_credentials`
- `confirm_no_real_money`
- `confirm_no_balance_credit`
- `confirm_no_real_receipt_generation`
- `confirm_no_pix_payment_execution`
- `confirm_no_secret_in_chat_or_docs`
- `confirm_no_env_file_printed_or_shared`
- `confirm_no_api_key_printed_or_shared`
- `confirm_no_webhook_token_printed_or_shared`
- `confirm_no_wallet_id_printed_or_shared`
- `confirm_no_onboarding_url_printed_or_shared`
- `confirm_payload_reviewed_locally`
- `confirm_payload_contains_no_placeholder_values`
- `confirm_response_sanitizer_enabled`
- `confirm_manual_execution_gate_reviewed`
- `confirm_single_controlled_attempt_only`
- `confirm_no_retry_loop`
- `confirm_manual_stop_on_unexpected_response`
- `confirm_sanitized_attempt_record_required`

## Manual controlled attempt checklist

Before any future `POST /accounts`, the operator must verify:

1. Repository state

   - `main` is clean
   - latest milestone tag is present locally and remotely
   - no uncommitted code or docs are present
   - no debug logging was added

2. Environment state

   - Sandbox base URL is selected
   - production base URL is not selected
   - Sandbox token is loaded from environment only
   - `.env` is not printed
   - token value is not copied to chat, commit, issue, PR body or docs

3. Payload state

   - payload fields are reviewed locally
   - no raw payload is committed
   - no raw payload is copied into chat
   - required subaccount fields are present
   - optional fields are intentionally omitted or documented
   - `apiKey`, `walletId`, `id` and `onboardingUrl` are never part of the request body

4. Execution state

   - manual operator is present
   - single attempt policy is active
   - no retry loop is enabled
   - timeout and stop conditions are understood
   - unexpected response stops the run immediately

5. Response state

   - response sanitizer is used immediately
   - raw response is not persisted
   - raw response is not copied to chat
   - `apiKey` is converted to a presence boolean or masked indicator
   - `walletId` is converted to a presence boolean or masked indicator
   - `id` is converted to a presence boolean or masked indicator
   - `onboardingUrl` is converted to a presence boolean or masked indicator
   - sanitized attempt record is created after the future attempt

## Allowed future sanitized evidence

A future controlled attempt record may expose only:

- `operation`
- `environment`
- `target_method`
- `target_path`
- `http_status_code`
- `request_executed`
- `subaccount_created`
- `object`
- `api_key_present`
- `wallet_id_present`
- `account_id_present`
- `onboarding_url_present`
- `sensitive_response_values_masked`
- `raw_response_stored`
- `raw_payload_stored`
- `real_money`
- `http_call_executed`
- `next_step_required`

## Forbidden evidence

A future controlled attempt record must never expose:

- access token
- API key
- webhook token
- `.env`
- raw request body
- raw response body
- raw error body
- raw headers
- `walletId` value
- `id` value
- `onboardingUrl` value
- `payment_id`
- `event_id`
- production credential
- production URL
- screenshot containing credentials

## Safety state

This milestone keeps:

- `first_controlled_subaccount_attempt_runbook_defined`: `true`
- `first_controlled_subaccount_attempt_executed`: `false`
- `subaccount_creation_executed`: `false`
- `manual_operator_review_required`: `true`
- `sandbox_base_url_confirmation_required`: `true`
- `environment_secret_loading_only_required`: `true`
- `no_production_credentials_required`: `true`
- `sanitized_response_required`: `true`
- `sanitized_attempt_record_required`: `true`
- `redacted_logs_only_required`: `true`
- `single_controlled_attempt_policy_required`: `true`
- `no_retry_loop_required`: `true`
- `manual_stop_on_unexpected_response_required`: `true`
- `raw_provider_payload_storage_allowed`: `false`
- `request_body_logging_allowed`: `false`
- `raw_provider_response_exposure_allowed`: `false`
- `stacktrace_exposure_allowed`: `false`
- `can_create_subaccount`: `false`
- `can_send_http`: `false`
- `network_call_allowed`: `false`
- `real_money`: `false`
- `http_call_executed`: `false`
- `ready_for_http_execution`: `false`

## Non-goals

This milestone does not implement an HTTP adapter, enable a network binding, define a send method, execute an Asaas request, create an Asaas subaccount, recover a real `onboardingUrl`, configure split, create a charge, generate a QR Code, receive a real payment, reconcile balances, test rate limits, test error cases, use production, move real money, expose secrets, expose raw payloads, expose raw responses, expose raw errors or expose stacktraces.

## Validation

Expected validation command:

`git diff --check`

No Python test count is expected to change in this documentation-only milestone.

## Next likely milestone

`v0.2.86-wallet-asaas-sandbox-subaccount-first-controlled-attempt-preflight-v1`
