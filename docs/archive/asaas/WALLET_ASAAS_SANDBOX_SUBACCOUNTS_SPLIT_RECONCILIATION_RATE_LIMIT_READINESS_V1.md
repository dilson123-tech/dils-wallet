# Wallet Asaas Sandbox Subaccounts, Split, Reconciliation and Rate Limit Readiness v1

## Delivery

Version: v0.2.77-wallet-asaas-sandbox-subaccounts-split-reconciliation-rate-limit-readiness-v1
Project: Aurea Gold / dils-wallet
Environment: Asaas Sandbox planning only
Production used: no
Real money moved: no

## Purpose

This document records the next Asaas Sandbox validation block requested after the successful webhook validation phase.

The previous webhook phase confirmed:

- asaas-access-token validation
- exclusive webhook token outside Git
- public temporary endpoint test
- PAYMENT_RECEIVED received with HTTP 200 OK
- idempotent webhook processing
- safe retry and replay handling
- safe audit record
- safe audit history
- no production usage
- no real money movement

This document prepares the next phase without executing any new external POST request.

## Support guidance received

The next Asaas validation block includes:

- test subaccounts
- validate permissions
- test onboardingUrl recovery if applicable
- validate returned data structure
- configure and test split if the operation will use split
- simulate a charge divided between accounts
- validate each split destination
- validate GET /v3/accounts/me/income
- compare income data with PAYMENT_RECEIVED webhooks
- confirm balance consistency
- test filters by period and status
- read rate and quota limit documentation
- test behavior near limits before production

## Safety position

This delivery is a readiness document only.

It does not:

- create subaccounts
- create payments
- configure real split
- query production
- move real money
- credit wallet balance
- generate real receipt
- mark real payment as paid
- expose API keys
- expose webhook tokens
- expose raw payment ids
- expose raw event ids
- expose raw payloads
- expose subaccount API keys
- expose wallet ids in public logs or chat

## Subaccounts readiness

### Goal

Prepare a controlled Sandbox validation for subaccounts before any production usage.

### Expected validation points

The subaccount validation should confirm:

- subaccount creation flow in Sandbox
- required request fields
- optional request fields
- returned account identifier
- returned wallet identifier
- returned API key handling rules
- permission model
- onboardingUrl availability if applicable
- pending documents flow if applicable
- safe storage requirements
- safe logging requirements

### Sensitive data classification

The following data must be treated as sensitive:

- subaccount API key
- parent account API key
- wallet id
- account id
- onboardingUrl
- personal or company document data
- phone number
- email
- address
- any full Asaas response payload

### Logging rule

Logs must never expose:

- full API key
- full wallet id
- full account id
- full onboardingUrl
- full document number
- full request body
- full response body

Allowed logging format:

- boolean flags
- status code
- provider name
- environment
- operation name
- sanitized result marker
- hashed or masked identifier if strictly required

### Planned result marker

A future successful controlled validation may use a marker like:

- ASAAS_SANDBOX_SUBACCOUNT_STRUCTURE_VALIDATED

Only after a controlled Sandbox test.

## onboardingUrl readiness

### Goal

Validate whether onboardingUrl applies to the dils-wallet model.

### Expected behavior

If onboardingUrl is returned or recovered, it must be handled as sensitive operational data.

### Safety rules

The onboardingUrl must not be:

- committed to Git
- pasted in chat
- exposed in public logs
- stored in plain frontend state
- exposed in screenshots

### Planned result marker

A future successful controlled validation may use a marker like:

- ASAAS_SANDBOX_ONBOARDING_URL_FLOW_VALIDATED

Only if this flow applies to the model.

## Split readiness

### Goal

Prepare split validation only if the commercial model requires payment split.

### Expected validation points

The split validation should confirm:

- whether dils-wallet needs split in the first commercial version
- which account creates the charge
- which destination accounts receive split amounts
- whether fixed value split is needed
- whether percentage split is needed
- how net amount is represented
- how fees affect final distribution
- how failed or refunded payments affect split entries
- how webhook status relates to split confirmation

### Safety rules

Before any split test:

- use Sandbox only
- use test subaccounts only
- use sanitized identifiers only
- do not expose wallet ids in chat
- do not use production account
- do not move real money
- do not credit internal real balance

### Planned result marker

A future successful controlled validation may use a marker like:

- ASAAS_SANDBOX_SPLIT_STRUCTURE_VALIDATED

Only after a controlled Sandbox test.

## Payment simulation readiness

### Goal

Prepare a future Sandbox charge simulation only if needed for split and reconciliation validation.

### Strict restrictions

A future payment simulation must:

- use Sandbox only
- use no real money
- not create a real receipt
- not credit real internal balance
- not mark real payment as paid
- not expose raw payment id
- not expose raw customer id
- not expose raw payload

### Required preconditions

Before any future controlled payment simulation:

- confirm current branch
- confirm clean Git state
- confirm .env is local and not committed
- confirm ASAAS_ENV=sandbox
- confirm REAL_MONEY_ENABLED=false
- confirm endpoint uses Sandbox base URL
- confirm no production credentials are loaded
- confirm request payload has no real customer-sensitive data

### Planned result marker

A future successful controlled validation may use a marker like:

- ASAAS_SANDBOX_SPLIT_PAYMENT_SIMULATION_VALIDATED

Only after explicit manual authorization.

## Reconciliation readiness

### Goal

Prepare reconciliation between Asaas income data and received PAYMENT_RECEIVED webhooks.

### Endpoint from support guidance

The support guidance mentioned:

- GET /v3/accounts/me/income

This endpoint must be validated in Sandbox before being treated as a stable integration dependency.

### Expected validation points

The reconciliation validation should compare:

- income status
- income value
- payment status
- payment date
- billing type
- webhook event type
- webhook received timestamp
- idempotency state
- internal audit status
- period filter behavior
- status filter behavior

### Internal consistency rule

A PAYMENT_RECEIVED webhook alone must not automatically create real money effects.

The reconciliation layer must confirm consistency before any future real-money feature is considered.

### Safe internal states

Recommended internal states for future planning:

- received_webhook
- replayed_webhook
- pending_reconciliation
- reconciliation_matched
- reconciliation_mismatch
- reconciliation_ignored
- reconciliation_error

### Mismatch handling

If reconciliation does not match webhook data:

- do not credit balance
- do not generate receipt
- do not mark payment as paid
- store safe audit marker
- require manual review
- avoid exposing raw payload

### Planned result marker

A future successful controlled validation may use a marker like:

- ASAAS_SANDBOX_RECONCILIATION_STRUCTURE_VALIDATED

Only after a controlled Sandbox read test.

## Rate limit and quota readiness

### Goal

Prepare the system to avoid surprise failures in production by respecting Asaas rate and quota limits.

### Expected validation points

The validation should confirm:

- documented request limits
- quota window behavior
- HTTP 429 behavior
- response headers related to rate limit
- retry-after or reset behavior when available
- safe backoff policy
- no aggressive polling
- no uncontrolled loops
- no bulk request storm

### Safety rule

Do not intentionally stress the Asaas Sandbox API without a controlled plan.

Near-limit behavior must be validated carefully and only if necessary.

### Recommended client behavior

The future Asaas client should:

- read rate limit headers when present
- stop or slow down when remaining requests are low
- use exponential backoff for transient errors
- avoid retrying non-retryable 4xx errors
- avoid parallel request storms
- log only sanitized rate limit metadata
- preserve user-facing stability during temporary Asaas throttling

### Planned result marker

A future successful controlled validation may use a marker like:

- ASAAS_SANDBOX_RATE_LIMIT_POLICY_VALIDATED

Only after documentation review or controlled Sandbox behavior validation.

## Proposed next technical sequence

Recommended safe order:

1. Document support guidance and readiness rules.
2. Prepare local guards for subaccount and split validation.
3. Add tests that block production usage.
4. Add tests that block real money movement.
5. Add sanitized response-shape validation.
6. Only then request explicit manual authorization for one controlled Sandbox POST, if needed.
7. Validate one step at a time.
8. Record evidence without secrets.

## Future delivery candidates

Suggested future deliveries:

- v0.2.78-wallet-asaas-sandbox-subaccount-structure-guard-v1
- v0.2.79-wallet-asaas-sandbox-subaccount-readiness-tests-v1
- v0.2.80-wallet-asaas-sandbox-split-structure-guard-v1
- v0.2.81-wallet-asaas-sandbox-reconciliation-readiness-v1
- v0.2.82-wallet-asaas-sandbox-rate-limit-policy-v1

The exact order may change after documentation review and implementation constraints.

## Current conclusion

The webhook phase is validated in Sandbox.

The next Asaas phase is not production enablement.

The next Asaas phase is controlled Sandbox readiness for:

- subaccounts
- onboardingUrl if applicable
- split
- income reconciliation
- rate limit and quota behavior

No production or real-money behavior should be enabled until the full partner and homologation requirements are clear.
