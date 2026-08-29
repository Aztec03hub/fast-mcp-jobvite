# ADR-0006: Single `main` branch rather than `main` plus `develop`

**Status:** Accepted
**Type:** Deviation

## Context

`devops/development-workflow.md:48-83` mandates a two-branch GitFlow with `main` and `develop`.

## Decision

Single `main`.

## Consequences

Defensible for a solo-maintained public integration, but it is a deviation from a required standard
and needs the record. **Scope of this ADR, stated because a narrow reading would leave two clauses
undisposed:**

- **B97, branch naming**, is an independent clause the branch-model deviation does not touch. It
  also collides with the ticket-prefix conflict noted in the ADR index.
- **The "merge only from develop or hotfix" half of B98** is necessarily voided by removing
  `develop`, and nothing else voids it on the record.
- **B99's four properties relocate onto `main` rather than retiring**: pull request, at least one
  approval, all CI green, branch current, squash merge.

