# Aurea Gold Wallet — Asaas Sandbox First Customer HTTP Transport Review V1

Milestone: v0.2.51-wallet-asaas-sandbox-first-customer-http-transport-review

## Purpose

This milestone reviews the safe design for the future HTTP transport that may execute the first controlled Asaas Sandbox customer call.

It is a technical review milestone only.

It does not implement a real HTTP transport and does not execute any external request.

## Current target

The first future external Sandbox call remains:

- Method: POST
- Path: /customers
- Operation: create_customer
- Base URL: https://sandbox.asaas.com/api/v3
- Environment: sandbox

This remains the safest first target because it does not create a Pix charge, does not retrieve a Pix QR Code, does not check payment status, does not move money, does not use split, does not use subaccounts and does not use production.

## Existing protection chain

The current protection chain is:

- strict Sandbox configuration guards;
- blocked production URL;
- real money disabled;
- secrets configured outside Git;
- manual execution gate;
- first HTTP call runbook;
- local preflight;
- client-side customer HTTP gate;
- HTTP transport still disabled.

## Transport requirements before implementation

Any future HTTP transport must keep these rules:

- use Sandbox base URL only;
- reject production URL before sending;
- require WALLET_MODE=partner;
- require WALLET_PARTNER_PROVIDER=asaas;
- require REAL_MONEY_ENABLED=false;
- require ASAAS_ENV=sandbox;
- require the official Sandbox URL;
- require local API Key without printing it;
- never log raw headers;
- never log access_token;
- never log webhook token;
- never log Wallet ID;
- never log full sensitive responses;
- never enable automatic execution;
- never retry blindly;
- never create Pix in this first customer step.

## Required request shape

The reviewed first request shape is:

- method: POST;
- path: /customers;
- operation: create_customer;
- body with fictitious customer data only;
- header access_token sourced from local environment only;
- no production credentials;
- no real customer data;
- no real CPF;
- no real email;
- no real phone;
- no real bank data;
- no Pix key.

## Approved fictitious payload class

The future payload may use only fictitious test data, such as:

- name: Cliente Sandbox Aurea Gold;
- cpfCnpj: fictitious test CPF only;
- email: cliente.sandbox@example.com;
- mobilePhone: fictitious test phone only.

## Forbidden data

The future request must not use:

- real customer name;
- real CPF or CNPJ;
- real email;
- real phone;
- real bank data;
- real Pix key;
- production API Key;
- webhook token in request body;
- Wallet ID;
- user personal data.

## Response handling requirements

A future transport must record only a safe result summary.

Allowed result fields:

- operation;
- environment;
- method;
- path;
- HTTP status code;
- success or failure;
- sanitized customer id, masked or omitted;
- timestamp;
- confirmation that no production call happened;
- confirmation that no real money moved;
- confirmation that no secrets were logged.

Forbidden result fields:

- API Key;
- access_token header;
- webhook token;
- Wallet ID;
- full raw response if sensitive;
- full raw headers;
- real customer data.

## Failure behavior

The future transport must stop immediately if:

- production URL is detected;
- real money flag is true;
- environment is not sandbox;
- provider is not asaas;
- API Key is missing;
- API Key looks like placeholder;
- manual authorization is missing;
- payload contains real-looking data;
- request target is not POST /customers;
- any Pix, QR Code, payment, split or subaccount operation is attempted.

## Manual authorization requirement

The mandatory phrase remains:

AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.

This review does not execute anything even if the phrase exists.

## Non-goals

This milestone does not:

- implement requests, httpx, aiohttp or urllib calls;
- send a request to Asaas;
- create a customer;
- create Pix;
- retrieve QR Code;
- check payment status;
- use production;
- move money;
- expose secrets.

## Validation

This is a documentation and transport review milestone.

Validation must include:

cd backend && pytest tests/test_asaas_config_guards.py tests/test_asaas_client_skeleton.py -q

Expected result:

32 passed

## Decision

The project is ready for a future controlled implementation of a Sandbox-only customer HTTP transport, but not for automatic execution.

The next implementation must still default to blocked execution and require explicit manual authorization.

## Next likely milestone

v0.2.52-wallet-asaas-sandbox-first-customer-http-transport-skeleton
