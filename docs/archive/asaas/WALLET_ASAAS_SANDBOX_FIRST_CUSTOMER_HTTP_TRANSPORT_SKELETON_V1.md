# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Transport Skeleton V1

Milestone: v0.2.52-wallet-asaas-sandbox-first-customer-http-transport-skeleton

## Purpose

This milestone adds the first safe HTTP transport skeleton for the future controlled Asaas Sandbox customer call.

The target remains:

- Method: POST
- Path: /customers
- Operation: create_customer
- Base URL: https://sandbox.asaas.com/api/v3
- Environment: sandbox

This milestone does not execute HTTP and does not send any request to Asaas.

## What changed

The client now has a transport skeleton result for the first customer HTTP call.

Added:

- AsaasFirstCustomerHttpTransportSkeletonResult
- build_first_customer_http_transport_skeleton
- tests proving the transport skeleton remains blocked
- tests proving the safe summary does not expose secrets

## Safety posture

The transport skeleton records intent and safety metadata only.

It keeps:

- http_transport_implemented: false
- http_transport_enabled: false
- retry_enabled: false
- real_money: false
- http_call_executed: false
- ready_for_http_execution: false

The access token header is only represented as configured or not configured.

The API Key value is never exposed.

## Manual authorization

The mandatory phrase may be recognized:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

Even when the phrase is present, this milestone still does not execute HTTP.

Manual authorization registered does not mean ready for HTTP execution.

## Explicit non-goals

This milestone does not:

- import requests;
- import httpx;
- import aiohttp;
- import urllib;
- open any network connection;
- send a request to Asaas;
- create a real customer;
- create a Pix charge;
- retrieve a Pix QR Code;
- check real payment status;
- use production;
- move real money;
- expose API Key;
- expose webhook token;
- expose Wallet ID.

## Safe result summary

The safe summary may include:

- operation;
- transport reference;
- prepared request summary;
- manual authorization status;
- access token header configured flag;
- timeout seconds;
- retry disabled flag;
- HTTP transport implemented flag;
- HTTP transport enabled flag;
- real money flag;
- HTTP call executed flag.

The safe summary must not include:

- API Key value;
- access_token value;
- webhook token value;
- Wallet ID;
- raw headers;
- raw sensitive response.

## Validation

Validation command:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Expected result:

34 passed

## Decision

The project now has a safe skeleton for the future HTTP transport, but the transport is still not implemented and not enabled.

The next step may be a stricter implementation review or a blocked transport adapter, still without executing a real Asaas request by default.

## Next likely milestone

v0.2.53-wallet-asaas-sandbox-first-customer-http-transport-adapter-gate
