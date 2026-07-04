# Wallet Asaas Sandbox Webhook Compliance Evidence v1

## Delivery

Version: v0.2.76-wallet-asaas-sandbox-webhook-compliance-evidence-v1
Project: Aurea Gold / dils-wallet
Environment: Asaas Sandbox only
Production used: no
Real money moved: no

## Purpose

This document records the current compliance evidence for the Asaas Sandbox webhook receiver implemented in dils-wallet.

The goal is to keep a safe technical record that can be used if Asaas requests confirmation about webhook validation, token handling, idempotency, retry behavior, audit evidence, and Sandbox readiness.

## Endpoint evidence

The Asaas Sandbox webhook receiver supports the safe webhook path:

- POST /api/v1/partners/asaas/webhooks/sandbox

A fallback route was also added for the path delivered by the Asaas Sandbox panel during testing:

- POST /api/v1/partners/
- POST /api/v1/partners

All supported routes use the same secure receiver logic.

## Header validation

The receiver validates the Asaas webhook token through the header:

- asaas-access-token

Observed behavior:

- missing header returns 401
- wrong header returns 403
- valid header returns 200

The token is not stored in Git.

## Configuration guard

The receiver uses the official Asaas Sandbox configuration guard.

Expected configuration:

- WALLET_MODE=partner
- WALLET_PARTNER_PROVIDER=asaas
- ASAAS_ENV=sandbox
- ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3
- REAL_MONEY_ENABLED=false
- ASAAS_API_KEY outside Git
- ASAAS_WEBHOOK_TOKEN outside Git

## Accepted event

The main accepted event is:

- PAYMENT_RECEIVED

Unsupported events are ignored safely.

## Idempotency

The receiver requires a unique event identifier and stores idempotency using the prefix:

- asaas-sandbox-webhook:*

Raw event identifiers are not exposed.

## Safe replay behavior

When Asaas retries or resends the same event, the receiver returns an explicit safe replay response.

Replay evidence includes:

- duplicated=true
- idempotency.replayed=true
- idempotency.state=replayed
- idempotency.replay_audit_status=asaas_sandbox_webhook_idempotent_replay
- audit.replay.safe_replay=true

Replay does not credit balance, generate receipt, or mark a real payment as paid.

## Safe audit record

The receiver stores a safe audit response in the idempotency response data.

Audit guarantees:

- provider=asaas
- environment=sandbox
- source=asaas_sandbox_webhook_receiver
- raw_payload_stored=false
- raw_event_id_stored=false
- raw_payment_id_stored=false
- real_money_enabled=false
- can_credit_balance=false
- can_generate_real_receipt=false
- can_mark_real_paid=false

No new database table or migration is required for this evidence record.

## Audit history

The project includes a safe audit history endpoint:

- GET /api/v1/partners/asaas/webhooks/sandbox/audit-history

The endpoint reads safe idempotency response records and filters only Asaas Sandbox webhook entries.

It does not expose:

- API key
- webhook token
- raw event id
- raw payment id
- raw payload

It does not:

- query real Asaas production transactions
- credit real balance
- generate real receipt
- mark real payment as paid

## Real Sandbox validation

A real Asaas Sandbox webhook delivery was validated through a public tunnel pointing to the local backend.

Observed result:

- HTTP 200 OK
- event delivered by Asaas Sandbox
- receiver accepted the request after token alignment
- no production environment used
- no real money moved

Internal status marker:

- ASAAS_SANDBOX_REAL_WEBHOOK_RECEIVED_OK

## Security limitations

This evidence intentionally does not include:

- ASAAS_API_KEY
- ASAAS_WEBHOOK_TOKEN
- raw payment id
- raw event id
- raw real payload
- active tunnel URL
- production credentials
- production transaction data

## Current conclusion

The Asaas Sandbox webhook receiver currently satisfies the expected Sandbox technical requirements for:

- secure token validation through asaas-access-token
- exclusive webhook token outside Git
- public endpoint test through tunnel
- PAYMENT_RECEIVED handling
- idempotent event processing
- safe retry/replay response
- safe audit record
- safe audit history
- no production usage
- no real money movement
- no raw sensitive identifier exposure

The next step is not to enable real money.

The next step is to use this evidence if Asaas requests confirmation, then ask Asaas for the next checklist toward pre-homologation or production readiness when appropriate.
