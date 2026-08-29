# ADR-0031: the registry has no row for a refused approval

**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change

> `DESIGN.md:513-521` names seven conditions and none of them is *"an approval was required and none
> was returned"*. Its catch-all sends anything unmapped to `/problems/internal-error`, **500** -
> which tells a caller this server is broken when a refusal is the control working exactly as
> designed. U10 reused `/problems/forbidden` rather than mint a slug, and correctly flagged that as
> an implementer's judgement rather than a decision. This ADR makes it a decision.

## Context

### The registry claims to be complete, and that claim is now false

`git show c15b138:docs/DESIGN.md`, immediately above the table:

> **"`:210` makes a published `type` URI a contract**, so inventing slugs is a promise we would owe
> forever. **The registry already has a type for every condition we produce.**"

That sentence was true when written. U10 produces a condition it does not cover, so the registry's
own completeness claim is what the new row repairs. **This is not a request to grow the registry
because a new error appeared; it is a repair of a statement the design makes about itself.**

### What the implementation did, and why it was right to flag it

`src/fast_mcp_jobvite/errors.py:201-213` raises `ApprovalRefusedError` against `FORBIDDEN`, with the
reasoning written into the class: no new slug, because `DESIGN.md:510` makes a published `type` a
promise owed forever; and not `/problems/internal-error`, because that would report a working control
as a broken server.

Both halves are right. What U10 could not do is decide whether widening the *"caller's token lacks
the scope"* row is legitimate, because that is a change to the frozen design.

## Decision

**Add a row: *"An approval was required and none was returned"* -> `/problems/forbidden`, 403.**

No new slug. The 403 row now names two conditions, and `detail` distinguishes them.

### The precedent is the design's own, and it is what makes this consistent rather than inventive

`DESIGN.md:356-359` already does exactly this, one row up:

> **"An open breaker is distinguishable from an outage without inventing a type.** Both use
> `/problems/service-unavailable` at 503, per the registry; what distinguishes them is `detail` ...
> An earlier revision minted two slugs for this. The distinction is real and worth making; a new
> contract-bearing type URI is not the way to make it."

Two conditions sharing one slug, separated by `detail`, is the pattern this design has already
chosen and already defended against the alternative. **A refused approval and a missing scope are the
same answer to the caller - "you are not permitted to do this" - differing in why.** The `why`
belongs in `detail`, exactly as the breaker's does.

## Consequences

### The status is 403 and the alternatives are worse

- **500** tells the caller the server failed. It did not; it refused, deliberately, and a caller that
  retries on 500 will keep hitting a control that will keep refusing.
- **422** is validation. The arguments were valid; the *permission* was absent.
- **A new slug** costs a promise owed forever, for a distinction `detail` already carries.

### `detail` is now load-bearing on the 403 row and must be asserted as such

Two conditions behind one slug means `detail` is the only thing separating them. The test for this is
not that a 403 came back - that passes for either condition. **Assert the detail text, and amputate
it:** make the refusal emit the scope row's detail and confirm the arm goes red. This project has a
recorded case of exactly this shape passing vacuously.

### It does not settle U10-F7, deliberately

`ApprovalState`'s vocabulary - `approved` / `refused` / `pending` / `unavailable` - is the
implementer's and not the design's. **ADR-0021 records what goes wrong when one ADR resolves two
things,** and ADR-0027 is already open in this neighbourhood. F7 gets its own decision or none; it
does not get folded in here because it happens to be nearby.

## What this ADR does not claim

**Not that any caller can currently reach this.** `create_candidate` is registered only when writes
are enabled AND the tool is named, and nothing proves a human approved anything - the README says so.
This makes the refusal path's error shape a decision rather than an accident; it does not change how
reachable that path is.
