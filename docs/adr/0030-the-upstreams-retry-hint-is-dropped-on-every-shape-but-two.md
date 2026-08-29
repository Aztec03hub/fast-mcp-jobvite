# ADR-0030: the upstream's retry hint is dropped on every shape but two

**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change

> When Jobvite returns a 5xx carrying a `Retry-After` we cannot afford within the outbound budget,
> the retry loop stops - correctly - and the failure surfaces as `/problems/external-service-error`
> 502 with the hint **discarded**. The caller learns *"Jobvite failed"* and not *"Jobvite said come
> back in 900 seconds"*, which is strictly less than we were told. This ADR decides that a hint the
> upstream volunteered is passed on wherever we have one.

## Context

### Where the hint currently survives, quoted at source

`src/fast_mcp_jobvite/services/jobvite_client.py:835-850` - `public_error()` attaches `retry_after`
on exactly one path:

```python
if self.cause.upstream_status == RATE_LIMITED_STATUS:
    return JobviteRetryLaterError(
        UNAVAILABLE_RATE_LIMITED_DETAIL,
        retry_after=self.retry_after,
        ...
    )
return self.cause
```

The frozen design, `git show c15b138:docs/DESIGN.md`, puts it in two places and both are 503s:

- `:356-359` - an open breaker and an outage share `/problems/service-unavailable`, distinguished by
  `detail` *"plus a `retry_after` hint"*.
- `:361-362` - *"Jobvite's `429`, if it exists, is retried and then mapped to 503, honouring
  `Retry-After` when present."*

**A 5xx carrying a `Retry-After` is not a shape the design contemplates.** That is why this is an
ADR: `r6-fixes` raised it and correctly declined to rule, and quietly attaching the field would be an
implementation inventing a contract - the move U6, U7 and U12 were each told to refuse.

### Why the obvious objection is weaker than it looks

The objection is that dropping the hint is harmless because a caller who retries immediately hits
**our** breaker and self-throttle rather than Jobvite, so the antisocial-retry harm is already
mitigated by machinery we own. That is true and it is not the point. The caller is an LLM deciding
whether to retry at all, and it is being handed the weaker of two facts we possess. **"We decided
not to tell you" is a worse answer than a documented field**, and this reads as a bug to whoever
first hits it.

### The fact that decides the cost, and it is not what the raising task assumed

Task #67 framed this as *"a change to the error contract's surface"* implying a new field on a fixed
schema. Measured, it is not. `src/fast_mcp_jobvite/errors.py:259` documents `**extensions` as
**"RFC 9457 extension members, e.g. the `retry_after` ..."**. The envelope already admits extension
members on any row; the registry declares `type`, `title` and `status` per row and does not enumerate
extensions.

So populating `retry_after` on a 502 **adds nothing to the registry and mints no new type URI.** It
populates a member the envelope has always permitted. RFC 9457 §3.2 exists for exactly this.

## Decision

**`retry_after` is populated wherever the upstream supplied one, on whatever problem shape results.**

It stays what it is: an optional RFC 9457 extension member. Absent means *we were not told*, never
*do not retry*. The two 503 shapes are unchanged - this widens where the hint may appear, and changes
nothing about where it already does.

**`retry_after` never becomes a required member and callers must tolerate its absence**, because the
common case remains no header at all: §4.4 records that Jobvite returns no rate-limit header and that
no 429 has ever been observed.

## Consequences

### It is a widening, and that is the whole reason it needed an ADR

A caller may now rely on the hint appearing on a 502. That is a promise, and promises are what the
frozen design exists to control. The cost of the ADR is not the code - it is a few lines - but the
commitment.

### The unaffordable-budget case is the one that motivated this and it deserves its own arm

The path is: a 5xx arrives with a `Retry-After` **larger than the outbound budget can absorb**, so
the retry loop stops rather than sleeping. That is the fix `r6-fixes` landed for M1 and it is right.
The hint is most valuable in exactly that case - it is the difference between *"failed"* and *"failed,
and it will keep failing for fifteen minutes"*.

### What must NOT happen when this is implemented

**Do not attach a hint we synthesised.** Only a value the upstream actually sent. A computed
`retry_after` on a 502 would be this server inventing a prediction and dressing it as the upstream's,
which is worse than the omission being fixed. The open-breaker 503's hint is computed from the
breaker's own remaining window and is ours to compute *because it describes our own state*; that
distinction is the rule.

**Do not let the test assert only presence.** A test that checks `retry_after` is in the envelope
passes against a hardcoded constant. Assert the **value** matches what the fake upstream sent, and
amputate it: return a different number from the fake and confirm the arm goes red.

## What this ADR does not settle

Whether any real Jobvite endpoint sends `Retry-After` on a 5xx. No credential exists to find out, and
§4.4 records that no rate-limit header is returned on any observed call. **This is written
defensively, like the 429 path it extends, and the implementing unit should say so rather than
implying the case has been seen.**
