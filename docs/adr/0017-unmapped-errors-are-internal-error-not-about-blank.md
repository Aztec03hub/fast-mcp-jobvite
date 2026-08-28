# ADR-0017: The unmapped row is `/problems/internal-error`, not `about:blank`

**Status:** Proposed
**Type:** Design change

> **Proposed.** This changes `DESIGN.md`, which is frozen, and it changes shipped behaviour in
> `errors.py`. It should be reviewed before it is applied — unlike ADR-0012 to 0014, which are held
> only on sequencing, this one has an argument someone might reject.

## Context

Found by **building U2**, not by reading. The design's error registry has an internal contradiction
and, underneath it, an answer the standard already supplies.

**The contradiction (D1).** `DESIGN.md:489-490` states that every failure returns a complete RFC
9457 problem object carrying *"`type`, `title`, `status`, `detail`, `instance`, `request_id`,
`timestamp`"* — `status` is a required member. `DESIGN.md:515`'s row reads:

```
| Anything unmapped | `about:blank` per `:212` | - |
```

The status column is `-`. **Both cannot hold**: either every problem object has a status, or the
unmapped one does not.

**The deeper issue (D2), and it is why this is not a one-character fix.**
`architecture/error-contract.md:115` scopes the fallback precisely:

> *"**`about:blank` fallback**: For unmapped **HTTP** errors, use `about:blank` as the type (per RFC
> 9457 §4.2.1)"*

That is about an unmapped **HTTP status received from somewhere**. It is not about an unhandled
exception inside our own tool body — and the same registry, at `error-contract.md:106`, already has
a row for exactly that:

```
| /problems/internal-error | 500 | Internal Server Error | Unhandled exception (generic safe message) |
```

So the design reached for the HTTP fallback in a case the registry already covers with a named type.

## Decision

**The unmapped row becomes `/problems/internal-error`, 500, "Internal Server Error".**

`about:blank` is retained for its actual scope — an unmapped **HTTP status** received from Jobvite,
where we genuinely have no type for what the upstream returned.

## Why this rather than filling in the blank

Adding `500` to the `about:blank` row would resolve D1 and leave D2 standing. It would also produce
the worse artifact: **a problem object with no type at all, in the one case a reader most wants a
type** — an unhandled exception in our own code, which is the failure a caller can do least about
and an operator most needs to grep for. `about:blank` is RFC 9457's way of saying *"no additional
semantics"*, and we have semantics here: it is ours, it is a bug, and the registry names it.

## Consequences

- **`errors.py` changes.** U2 implemented `about:blank` + 500 per RFC 9457 §4.2.1 and said plainly
  that this was *its reading, not the design's instruction*. Under this ADR that reading is replaced,
  and **U2's mutant M10 — which the harness killed — becomes correct behaviour.** That inversion is
  the clearest evidence this is a real change rather than a tidy-up.
- **`INTERNAL_ERROR` stops being dead code.** U2 reported that the constant is defined and reached
  by no code path. Under the design as frozen it should be deleted; under this ADR it is the answer.
  **The dead constant was the symptom.**
- **`DESIGN.md:515` is amended**, and `:489-490`'s seven-member requirement then holds without
  exception — which is the property that makes the error contract checkable at all.
- **No threat-model row changes.** This alters which type an unhandled exception carries, not
  whether one is emitted or what it discloses. The generic-safe-message property is unchanged, and
  is what keeps an internal error from leaking a stack trace.

## What this ADR does not settle

**Whether `about:blank` is ever actually reachable.** It survives for unmapped HTTP statuses from
Jobvite — but §5.1's registry maps every status this client is known to receive, so the fallback may
be unreachable in practice. Establishing that needs the live-tenant observations the credential
checklist gates, and **an unreachable fallback that is correct is better than a reachable one that
is wrong**, so it stays either way.
