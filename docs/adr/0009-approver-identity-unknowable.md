# ADR-0009: Approver identity cannot be recorded. Caller identity can, on HTTP.

**Status:** Accepted

## Context

`ai/agent-guardrails.md:79` requires recording who approved what and when.

## Decision

Record that an approval response was received and what it said. Do not claim to record who approved.

## Consequences

A host may auto-respond to elicitation with no human present - Claude Code documents a hook that
does exactly this - and the MCP specification places human-in-the-loop confirmation on the host, not
the server. **So the honest claim is that the server requires an approval response from the host and
refuses to write without one, never that a human approved.**

**This ADR is scoped to the approver and explicitly not to the caller.** Two different identities
are in play and conflating them would close a gap this decision never considered:

- **Who approved** is unknowable, as above.
- **Which client invoked the tool** is knowable **on the HTTP transport**, where the rate limiter
  already derives it, and it is recorded.
- **On stdio there is no client identity**, because there is no token. The audit event states that
  attribution is unavailable rather than emitting the literal `"global"` and implying an identity.

