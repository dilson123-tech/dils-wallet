# GitHub Governance — Aurea Gold

## Purpose

This document defines the repository protection and pull request flow for the `main` branch of Aurea Gold.

The goal is to keep the product repository safe, predictable, and aligned with a fintech-grade delivery process.

## Protected Branch

The `main` branch is protected by the active ruleset:

- `aurea-main-guard`

Target:

- `refs/heads/main`

## Main Protections

The current ruleset protects `main` against:

- branch deletion
- non-fast-forward updates
- direct unsafe changes outside the expected PR flow

## Pull Request Rule

Changes must go through pull requests before reaching `main`.

Current pull request settings:

- required approving review count: `0`
- code owner review: `false`
- require last push approval: `false`
- required review thread resolution: `false`

This means the repository currently enforces PR-based delivery, while relying primarily on required status checks rather than mandatory review approval.

## Required Status Checks

The `main` branch currently requires these checks to pass:

- `lint`
- `smoke`

Strict status checks policy is enabled.

This means the pull request branch must be in a valid and up-to-date state relative to `main` when required by GitHub protection rules.

## CI Alignment Note

A previous merge block happened because the repository ruleset required the `smoke` check, while the workflow configuration did not expose that check on pull requests.

This was corrected by allowing the smoke workflow to run on `pull_request`, keeping CI behavior aligned with branch protection expectations.

## Practical PR Flow

Recommended delivery flow:

1. create a feature or docs branch
2. make a small, controlled change
3. run local validation when applicable
4. push the branch
5. open a pull request against `main`
6. wait for required checks (`lint` and `smoke`)
7. merge only after checks are green
8. sync local `main`

## Operational Guidance

When a pull request is blocked:

1. inspect PR checks first
2. confirm required check names match the ruleset exactly
3. inspect workflow triggers (`push`, `pull_request`, `workflow_dispatch`)
4. verify whether the blocked item is CI, ruleset naming, or branch freshness
5. only then change code or workflows

Do not assume a product bug when the block is caused by governance or CI mismatch.

## Strategic Recommendation

Current governance is solid and lightweight, but future hardening may include:

- requiring at least 1 approval review
- documenting ownership rules
- reviewing whether `lint` and `smoke` remain the ideal minimum gate set
- periodically auditing ruleset/check name alignment

## Status

This document is part of the Aurea Gold production governance baseline.
