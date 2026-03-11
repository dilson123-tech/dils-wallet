[![Smoke Prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke_prod.yml/badge.svg)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke_prod.yml)
[![smoke-prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke.yml/badge.svg?branch=main)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke.yml)
[![health-prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/health.yml/badge.svg?branch=main)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/health.yml)

# Aurea Gold

**Aurea Gold** is a production-oriented digital wallet and PIX platform designed for real-world financial operations.  
It combines a FastAPI backend, premium client/admin panels, secure authentication flows, idempotent payment processing, CI automation, and deploy-ready infrastructure.

## Overview

Aurea Gold was built as a real fintech product foundation — not just a demo API.  
The project focuses on reliability, payment integrity, operational clarity, and a premium user experience for both customers and administrators.

Core goals:

- provide a modern digital wallet foundation
- support PIX-based payment flows
- guarantee safe request replay with idempotency
- offer separate premium panels for client and admin use
- maintain production discipline with CI, smoke tests, and structured documentation

## Main Features

- Digital wallet backend built with **FastAPI**
- PIX transfer flow with **idempotency protection**
- JWT-based authentication
- Premium client-facing interface
- Admin panel for operational control
- PostgreSQL-ready environment
- Railway deployment support
- CI workflows and smoke test structure
- Documentation and scripts for local/dev operations

## Architecture

This repository contains the core layers of the Aurea Gold platform:

- `backend/` — FastAPI backend, business rules, auth, wallet and PIX flows
- `frontend/` — front-end application layer
- `aurea-gold-client/` — premium client panel
- `aurea-gold-admin/` — premium admin panel
- `docs/` — technical and product documentation
- `.github/` — CI workflows and repository automation
- `scripts/` — helper scripts for development and operational routines
- `tests/` — automated validation and reliability checks

## Product Positioning

Aurea Gold is treated as a **real commercial product** with production mindset:

- stability before visual changes
- deterministic debugging before guesswork
- controlled payment flows
- clear separation between validated behavior and future improvements
- documentation aligned with actual implementation

## PIX Flow Reliability

One of the key platform concerns is payment integrity.

The PIX sending flow is designed to support:

- first execution of a payment request
- safe replay of the same request using the same `Idempotency-Key`
- conflict protection when the same key is reused with a different payload
- response signaling for replayed requests

This helps prevent duplicated operations and supports safer client integrations.

## Tech Stack

- **Backend:** FastAPI, Python
- **Database:** PostgreSQL
- **Auth:** JWT
- **Frontend:** React / TypeScript
- **Infra / Deploy:** Railway
- **Version Control / CI:** GitHub Actions

## Current Focus

The current product phase is focused on:

- strengthening public repository presentation
- improving technical documentation
- making real platform capabilities visible on GitHub
- consolidating product governance and roadmap visibility

## Running Locally

Example local backend flow:

    cd ~/dils-wallet/backend
    source .venv/bin/activate
    export DATABASE_URL='postgresql://aurea:aurea123@127.0.0.1:55440/aurea'
    uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload --log-level debug

Health check:

    curl -i http://127.0.0.1:8090/healthz

## Development Principles

This repository follows a practical engineering playbook:

- do not debug blindly
- capture request, response, status, and backend logs first
- validate health before changing code
- prefer small patches over large rewrites
- validate behavior before touching interface
- treat stable flows as protected assets

## Roadmap

Planned improvements include:

- stronger public product documentation
- expanded PIX flow documentation
- repository hygiene and visual organization
- clearer governance through issues and milestones
- product-level security and operational hardening

## Status

Aurea Gold is an active, evolving fintech product under structured development, with focus on production readiness, payment reliability, and premium delivery quality.

## Author

Developed by **Dilson Pereira**  
GitHub: [dilson123-tech](https://github.com/dilson123-tech)
