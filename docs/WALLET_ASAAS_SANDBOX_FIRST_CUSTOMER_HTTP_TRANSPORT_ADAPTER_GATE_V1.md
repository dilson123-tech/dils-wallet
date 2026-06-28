# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Transport Adapter Gate V1

Milestone: v0.2.53-wallet-asaas-sandbox-first-customer-http-transport-adapter-gate

## Purpose

This milestone adds a blocked adapter gate for the future controlled Asaas Sandbox customer HTTP transport.

The target remains:

- Method: POST
- Path: /customers
- Operation: create_customer
- Base URL: https://sandbox.asaas.com/api/v3
- Environment: sandbox

This milestone does not implement a real HTTP adapter and does not send any request to Asaas.

## What changed

Added:

- AsaasFirstCustomerHttpTransportAdapterGateResult
- gate_first_customer_http_transport_adapter
- adapter safety metadata
- tests proving the adapter gate remains blocked
- tests proving the safe summary does not expose secrets

## Adapter gate behavior

The adapter gate validates the intended first customer target and records safety state.

It keeps:

- sandbox_only: true
- target_allowed: true for POST /customers create_customer
- adapter_implemented: false
- adapter_enabled: false
- can_send_http: false
- retry_enabled: false
- real_money: false
- http_call_executed: false
- ready_for_http_execution: false

## Manual authorization

The mandatory phrase may be recognized:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

Even when the phrase is recognized, the adapter cannot send HTTP.

Manual authorization registered does not enable the adapter.

## Explicit non-goals

This milestone does not:

- import requests;
- import httpx;
- import aiohttp;
- import urllib;
- implement a network adapter;
- open a network connection;
- execute HTTP;
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
- adapter reference;
- adapter name;
- prepared request summary;
- manual authorization status;
- access token header configured flag;
- sandbox-only flag;
- target allowed flag;
- adapter implemented flag;
- adapter enabled flag;
- can send HTTP flag;
- retry disabled flag;
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

36 passed

## Decision

The project now has a blocked adapter gate for the future Asaas Sandbox POST /customers transport.

The adapter is still not implemented, not enabled and cannot send HTTP.

## Next likely milestone

v0.2.54-wallet-asaas-sandbox-first-customer-http-blocked-adapter-contract
