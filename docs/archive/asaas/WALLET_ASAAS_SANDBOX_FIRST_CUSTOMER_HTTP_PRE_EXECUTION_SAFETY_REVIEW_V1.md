# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Pre-Execution Safety Review V1

Milestone: v0.2.57-wallet-asaas-sandbox-first-customer-http-pre-execution-safety-review

## Purpose

This milestone adds a pre-execution safety review for the future first Asaas Sandbox POST /customers HTTP call.

The goal is to confirm that the project has enough documented safeguards before any future controlled Sandbox HTTP execution is considered.

This milestone still does not implement a real HTTP adapter and does not send any request to Asaas.

## Confirmed Asaas target

The future target remains:

- Base URL: https://sandbox.asaas.com/api/v3
- Method: POST
- Path: /customers
- Operation: create_customer
- Authentication header name: access_token
- Environment: sandbox

## Current safety chain

The current safety chain before any future HTTP execution is:

1. Preflight validation
2. Client gate
3. Transport review
4. Transport skeleton
5. Adapter gate
6. Blocked adapter contract
7. Response sanitizer contract
8. Error sanitizer contract
9. Pre-execution safety review

## Required pre-execution conditions

Before any future first Sandbox HTTP execution, all of the following must be true:

- branch must be based on main;
- main must be aligned with origin/main;
- local working tree must be clean;
- tests must pass;
- git diff --check must pass;
- production must remain blocked;
- real money must remain disabled;
- Asaas base URL must be Sandbox only;
- operation must remain POST /customers only;
- adapter implementation must be explicitly reviewed;
- manual authorization must be explicitly registered;
- secrets must never be printed;
- raw provider response must not be exposed;
- raw provider error must not be exposed;
- request body must not be exposed in logs;
- stacktrace must not be exposed in safe summaries;
- access_token value must never appear in logs, summaries, docs or tests;
- webhook token value must never appear in logs, summaries, docs or tests;
- Wallet ID must never appear in logs, summaries, docs or tests.

## Current blocked state

At this milestone, the project must still remain blocked:

- no HTTP adapter implementation;
- no HTTP execution;
- no Asaas request;
- no customer created in Asaas;
- no Pix charge created;
- no Pix QR Code retrieved;
- no payment status checked;
- no production usage;
- no real money movement;
- no raw provider payload exposure;
- no secret exposure.

## Manual authorization phrase

The mandatory phrase remains:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

This phrase alone does not execute HTTP.

The phrase only records human authorization intent. It does not enable adapter execution by itself.

## Safety review checklist

A future execution branch must explicitly verify:

- environment is sandbox;
- production URL is not used;
- access_token header name is configured without exposing its value;
- request target is POST /customers;
- request payload contains only the approved first customer fields;
- response sanitizer is active before any response is surfaced;
- error sanitizer is active before any error is surfaced;
- raw response retention is disabled;
- raw error retention is disabled;
- request body logging is disabled;
- stacktrace exposure is disabled;
- tests cover blocked and authorized states;
- CI checks are green;
- manual review is recorded.

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
- expose access_token value;
- expose webhook token;
- expose Wallet ID;
- expose headers;
- expose request body;
- expose raw response;
- expose raw error;
- expose raw provider error;
- expose stacktrace.

## Validation

Expected validation before merging this milestone:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Expected result:

42 passed

## Decision

The project now has a documented pre-execution safety review for the future first Asaas Sandbox POST /customers call.

The adapter is still not implemented, not enabled and cannot send HTTP.

## Next likely milestone

v0.2.58-wallet-asaas-sandbox-first-customer-http-manual-execution-approval-gate
