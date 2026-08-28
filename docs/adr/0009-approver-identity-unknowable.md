# ADR-0009: Approver identity cannot be recorded. Caller identity can, on HTTP.

**Status:** Accepted

## Context

`ai/agent-guardrails.md:77-79` reads, whole:

> *"**Approvals are scoped and expire.** An approval authorizes one specific call (or a narrow,
> declared batch), not a standing capability. Record *who* approved *what* and *when* in the audit
> log."*

**The bullet has two halves and this ADR disposes of one of them.** The citation here was `:79`
alone until the CONF-5 citation-range audit; a reader could reasonably have taken the whole bullet
as scoped out, which it is not.

- **`:77-78`, scoped-and-expires: SATISFIED, not scoped out.** MRTR binds an approval to the retry
  of the exact call it was requested for (`DESIGN.md` §7.5), so an approval cannot become a standing
  capability - there is no token to carry forward and no batch to widen. §7.6 records that the one
  mechanism which could have created a standing grant, the confirmation token, was cut.
- **`:79`, record who approved: the subject of this ADR**, below.

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

