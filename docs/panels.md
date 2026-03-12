# Aurea Gold — Product Panels Overview

## Objective

This document summarizes the role of the client and admin panels inside Aurea Gold.

It exists to make the public product structure easier to understand from a repository and product-governance perspective.

## Client Panel

The client panel represents the user-facing surface of Aurea Gold.

Its role is to support the premium product experience around wallet usage, authenticated flows, and financial interaction from the end-user perspective.

## Admin Panel

The admin panel represents the operational and governance surface of Aurea Gold.

Its role is to support internal visibility, administrative controls, and product-level operational management.

## Separation of Responsibilities

Client and admin surfaces should remain clearly separated in purpose and evolution.

This helps preserve:
- safer product changes
- clearer governance
- cleaner operational reasoning
- better long-term maintainability

## Product Governance View

Panels are treated as real product surfaces, not as decorative frontends attached to an API.

Because of that, changes affecting these surfaces should be evaluated according to user impact, operational impact, and alignment with the active product path.

## Near-Term Focus

- keep the official client/admin distinction clear
- improve public documentation of each surface
- reduce ambiguity between active panels and old, legacy, or lab artifacts when possible
