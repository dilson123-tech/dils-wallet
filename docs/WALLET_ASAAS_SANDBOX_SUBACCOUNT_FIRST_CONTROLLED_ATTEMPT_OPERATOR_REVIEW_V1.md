# Aurea Gold Wallet — Asaas Sandbox Subaccount First Controlled Attempt Operator Review V1

Milestone: `v0.2.87-wallet-asaas-sandbox-subaccount-first-controlled-attempt-operator-review-v1`

## Purpose

This milestone records the manual operator review required before any future first controlled Asaas Sandbox subaccount attempt.

The review sits after the non-executing runbook and the first controlled attempt preflight. It confirms what an operator must inspect before any future `POST /accounts` attempt can even be considered.

This milestone does not execute HTTP.

## Scope

The operator review is built on top of:

- `v0.2.85-wallet-asaas-sandbox-subaccount-first-controlled-attempt-runbook-v1`
- `v0.2.86-wallet-asaas-sandbox-subaccount-first-controlled-attempt-preflight-v1`

The review is documentation-only and does not add an HTTP adapter, enable network execution, create a subaccount, call Asaas, expose secrets or move money.

## Target Asaas operation under review

- Environment: Sandbox only
- Base URL: `https://sandbox.asaas.com/api/v3`
- Method: `POST`
- Path: `/accounts`
- Operation: `create_subaccount`
- Authentication model: environment-loaded `access_token` only
- Payload policy: reviewed locally, never printed or committed
- Response policy: sanitizer required immediately after any future response
- Attempt policy: single controlled attempt only in a future milestone
- Retry policy: no retry loop
- Stop policy: manual stop on unexpected response

## Operator review status

The current review status is:

- `operator_review_record_defined`: `true`
- `operator_review_completed`: `false`
- `operator_approval_to_execute_http`: `false`
- `first_controlled_subaccount_attempt_executed`: `false`
- `subaccount_creation_executed`: `false`
- `can_create_subaccount`: `false`
- `can_send_http`: `false`
- `network_call_allowed`: `false`
- `real_money`: `false`
- `http_call_executed`: `false`
- `ready_for_http_execution`: `false`

This milestone is a review record, not an execution approval.

## Manual operator review checklist

Before any future attempt, the operator must verify:

1. Repository state

   - `main` is clean
   - latest tag is present locally
   - latest tag is present remotely
   - no uncommitted files exist
   - no debug logging was added
   - no temporary script contains secrets
   - no raw request or raw response fixture contains real provider data

2. Environment state

   - Sandbox environment is selected
   - production environment is not selected
   - Sandbox base URL is used only as configuration
   - production base URL is not used
   - token is loaded from environment only
   - `.env` is not printed
   - no API key or webhook token is copied to chat, docs, issues, PR body or logs

3. Payload state

   - payload builder guard has already been reviewed
   - payload shape matches the subaccount contract
   - required fields are present
   - optional fields are intentionally omitted or documented
   - no placeholder payload is sent
   - no raw payload is committed
   - no raw payload is copied to chat
   - `apiKey`, `walletId`, `id` and `onboardingUrl` are never request-body inputs

4. Manual gate state

   - manual authorization phrase is not treated as automatic execution
   - manual execution gate remains non-executing
   - preflight remains non-executing
   - `can_send_http` remains `false`
   - `can_create_subaccount` remains `false`
   - `network_call_allowed` remains `false`
   - `http_call_executed` remains `false`

5. Execution control state

   - operator is present
   - single-attempt policy is understood
   - no retry loop is enabled
   - timeout and stop criteria are understood
   - unexpected response stops the run immediately
   - no follow-up attempt happens automatically
   - no production fallback exists

6. Response handling state

   - response sanitizer is required
   - raw response is not persisted
   - raw response is not copied to chat
   - raw error body is not copied to chat
   - raw headers are not copied to chat
   - `apiKey` is reduced to a presence boolean or masked indicator
   - `walletId` is reduced to a presence boolean or masked indicator
   - `id` is reduced to a presence boolean or masked indicator
   - `onboardingUrl` is reduced to a presence boolean or masked indicator
   - sanitized attempt record is required in a future milestone

## Operator review confirmations

The operator review requires these confirmations before any future execution milestone:

- `confirm_main_branch_clean_and_tagged`
- `confirm_latest_tag_is_v0_2_87_or_later`
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
- `confirm_payload_builder_guard_reviewed`
- `confirm_payload_reviewed_locally`
- `confirm_response_sanitizer_enabled`
- `confirm_manual_execution_gate_reviewed`
- `confirm_first_controlled_attempt_preflight_reviewed`
- `confirm_single_controlled_attempt_only`
- `confirm_no_retry_loop`
- `confirm_manual_stop_on_unexpected_response`
- `confirm_sanitized_attempt_record_required`

## Allowed review evidence

This operator review may expose only:

- milestone name
- repository branch name
- repository tag name
- sanitized checklist status
- boolean gate status
- target method
- target path
- target environment
- safety flags
- validation command names
- next milestone name

## Forbidden review evidence

This operator review must never expose:

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
- real `payment_id`
- real `event_id`
- production credential
- production URL
- screenshots containing credentials

## Safety state

This milestone keeps:

- `operator_review_record_defined`: `true`
- `operator_review_completed`: `false`
- `operator_approval_to_execute_http`: `false`
- `manual_operator_review_required`: `true`
- `first_controlled_attempt_preflight_required`: `true`
- `sandbox_base_url_confirmation_required`: `true`
- `environment_secret_loading_only_required`: `true`
- `no_production_credentials_required`: `true`
- `payload_builder_guard_required`: `true`
- `response_sanitizer_required`: `true`
- `sanitized_attempt_record_required`: `true`
- `redacted_logs_only_required`: `true`
- `single_controlled_attempt_policy_required`: `true`
- `no_retry_loop_required`: `true`
- `manual_stop_on_unexpected_response_required`: `true`
- `raw_payload_storage_allowed`: `false`
- `raw_response_storage_allowed`: `false`
- `request_body_logging_allowed`: `false`
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

`v0.2.88-wallet-asaas-sandbox-subaccount-first-controlled-attempt-evidence-template-v1`
