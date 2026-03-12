# Aurea Gold — Architecture Overview

## Product Positioning

Aurea Gold is a production-oriented fintech platform focused on digital wallet operations, PIX flows, admin governance, and premium client experience.

The repository is structured as a multi-surface product base, not as a minimal API-only project.

## Main Product Surfaces

### 1. Backend
- FastAPI-based application core
- authentication and protected routes
- PIX-related flows and idempotency rules
- health, readiness, and observability endpoints
- governance and service-layer logic

### 2. Client Panel
- user-facing product surface
- premium wallet experience
- payment and PIX interaction flows
- authenticated frontend experience

### 3. Admin Panel
- operational and governance surface
- administrative monitoring and controls
- internal product management workflows

## Architectural Direction

Aurea Gold is organized around clear separation of concerns between API/backend responsibilities, client experience, and administrative operations.

This separation supports product evolution, safer delivery, and clearer governance of critical fintech flows.

## Engineering Principles

- production-oriented repository governance
- protected main branch through pull-request rulesets
- required status checks before merge
- observable health and smoke validation
- objective maturity tracking by product area

## Near-Term Architecture Focus

- keep backend, client, and admin boundaries explicit
- strengthen public technical documentation
- preserve merge discipline and operational confidence
- reduce ambiguity between active product paths and legacy or lab artifacts
