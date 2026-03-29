[![Smoke Prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke_prod.yml/badge.svg)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke_prod.yml)
[![smoke-prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke.yml/badge.svg?branch=main)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/smoke.yml)
[![health-prod](https://github.com/dilson123-tech/dils-wallet/actions/workflows/health.yml/badge.svg?branch=main)](https://github.com/dilson123-tech/dils-wallet/actions/workflows/health.yml)

# Aurea Gold

**Aurea Gold** is a production-grade digital wallet and PIX platform built for real financial operations.

Designed with reliability, payment integrity, and operational discipline at its core, Aurea Gold is not a demo system — it is a fintech foundation ready for real-world usage.

## What Aurea Gold Is

Aurea Gold is a complete digital wallet platform that enables:

- PIX-based payments
- secure authentication flows
- controlled financial operations
- premium interfaces for both clients and administrators

The system is built with a **production-first mindset**, ensuring that every validated behavior is deterministic and reliable.

## Why It Matters

Financial systems cannot afford ambiguity.

Aurea Gold focuses on:

- preventing duplicated transactions
- ensuring safe request replay
- delivering clear operational feedback
- maintaining strict backend validation rules

This approach reduces risk and increases trust for both users and integrators.

## Validated Capabilities

The platform already includes:

- JWT authentication
- health and readiness endpoints
- PIX send flow (`/api/v1/pix/send`)
- idempotency protection
- replay-safe requests (same key → same response)
- conflict detection (same key + different payload → `409 Conflict`)
- CI workflows for lint, tests, smoke, and health validation

## PIX Flow Reliability

The PIX operation supports:

- first execution → `200 OK`
- replay with same payload → `200 OK` + `x-idempotency-replayed: true`
- conflict with same key and different payload → `409 Conflict`

No duplicated records are created.

This ensures safer financial operations even under retry scenarios and strengthens integration reliability for client applications.

## Platform Structure

- `backend/` — FastAPI core, wallet logic, PIX, auth
- `frontend/` — base application layer
- `aurea-gold-client/` — premium client panel
- `aurea-gold-admin/` — premium admin panel
- `docs/` — technical and product documentation
- `.github/` — CI workflows and repository automation
- `scripts/` — development and operational utilities
- `tests/` — validation and safety checks

## Documentation

Detailed project documentation is available in:

- `docs/architecture.md`
- `docs/deploy.md`
- `docs/pix-operation.md`
- `docs/panels.md`
- `docs/product-maturity.md`

## Tech Stack

- **Backend:** FastAPI / Python
- **Database:** PostgreSQL
- **Auth:** JWT
- **Frontend:** React / TypeScript
- **Infra / Deploy:** Railway
- **CI/CD:** GitHub Actions

## Running Locally

Example backend flow:

```bash
cd ~/dils-wallet/backend
source .venv/bin/activate
export DATABASE_URL='postgresql://aurea:aurea123@127.0.0.1:55440/aurea'
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload --log-level debug
```

Health check:

```bash
curl -i http://127.0.0.1:8090/healthz
```

## Engineering Principles

This repository follows a practical engineering playbook:

- deterministic debugging first
- no blind fixes
- validate health before changing code
- prefer small patches over large rewrites
- validate backend behavior before touching interface
- protect stable flows as product assets

## Current Focus

The current product phase is focused on:

- strengthening public repository presentation
- improving technical documentation
- exposing validated platform capabilities more clearly
- consolidating governance and product visibility

## Status

Aurea Gold is an active fintech product under structured development, focused on production readiness, payment reliability, and premium delivery quality.

## Author

Developed by **Dilson Pereira**  
GitHub: [dilson123-tech](https://github.com/dilson123-tech)
