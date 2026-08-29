# ADR-0005: The `ai/` standards domain binds this repository by intent

**Status:** Accepted
**Type:** Deviation

## Context

`ai/README.md:22-33` scopes the domain to product code that **calls** foundation models. This server
calls none; models call it. Read literally, `ai/tool-calling.md` and `ai/agent-guardrails.md` do not
reach us - and those are the only documents in the estate describing how to define a tool safely.

## Decision

They bind.

## Consequences

The risk model those documents govern is tool-definition safety, destructive-operation gating, and
injection through attacker-authored content. **An MCP server is precisely that surface with the
direction of the call reversed.** Excusing ourselves on a scoping technicality would ship the one
component in the estate that is entirely a tool catalogue for a model, governed by nothing.

Obligations B9-B26 apply in full: typed schemas per tool, default-deny on destructive operations,
and candidate-authored content treated as hostile.

