# ADR-0033: `approval_state`'s four values are a published vocabulary

**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change

> `ApprovalState`'s four values - `approved`, `pending`, `refused`, `unavailable` - were chosen by
> U10 and named in `approval.py` as its own choice, "reported rather than presented as settled".
> ADR-0021 declined to fold the question in. This settles it: the values are right, and **they
> belong in the design, because they are already published** - `approval_state` is a mandated field
> of the audit event, and the audit event is a compliance artefact.

## Context

### ADR-0021's restraint was correct and is the reason this is cheap

`approval.py:183-189` records that ADR-0021 *"explicitly does NOT settle this vocabulary ... because
one ADR resolving two things is how the half nobody was looking at ships unreviewed"*. U10 then
emitted its chosen values with a comment saying they were its choice rather than a decision. Because
it did that instead of quietly shipping them as settled, this ADR is a ruling rather than an
excavation.

### The values are not an implementation detail, and that is what decides it

The test for "should the design name these?" is whether anything outside the implementation depends
on the distinction. It does, and the design already says so:

- `DESIGN.md:678` - *"**The audit event includes `approval_state`.** `agent-guardrails.md:121-123`
  names it explicitly"*.
- `DESIGN.md:1756`, threat row **C4-R1**, rated **High**: *"The approval decision is not among the
  audited fields, so there is no record that a gated write was authorised"*, mitigated by the audit
  event carrying `approval_state`.

**A field a High threat row is mitigated by is not an implementation detail, and its VALUES are what
the mitigation actually consists of.** `audit.py:205` puts it on the wire.

### All four are reachable, checked rather than assumed

Constructed in `src/`: `APPROVED` 2 sites, `REFUSED` 2, `PENDING` 1, `UNAVAILABLE` 1. **None is
unreachable** - which mattered to check first, because an unreachable value reads as discharged and
would have changed what this ADR should say. That is U5's note about the structural limits and the
same reasoning ADR-0029 turned on.

## Decision

**The four values are correct and `DESIGN.md` §5.3 names them as a closed set.**

Each earns its place by answering a different question a compliance reader asks:

| value | what happened | did a write occur |
|---|---|---|
| `approved` | a response arrived and authorised it | yes |
| `refused` | a response arrived and did not | no, and a human said so |
| `pending` | asked, no answer yet | not yet, and **maybe never** |
| `unavailable` | could not ask at all | no, and nobody was asked |

**`pending` and `unavailable` are the pair most likely to be collapsed, and they must not be.**
`pending` means the MRTR first leg went out and the answer never came - `approval.py:195-197` records
that an approval abandoned there is C4-D1, *"the call hangs with no server-side bound, so this is the
last audit record such an invocation ever produces"*. `unavailable` means no handler existed to ask.
One is an abandoned conversation, the other a conversation that never started; collapsing them makes
an abandoned approval indistinguishable from an unconfigured host in the only record either leaves.

`refused` and `unavailable` are the same distinction one step over: *a human said no* versus *no
human was asked*.

## Consequences

### The set is CLOSED, and a fifth value is an ADR

The same rule ADR-0028 applies to `ApprovalMechanism`. A unit that needs a fifth state has found
something the design does not model, and inventing a string for it decides a published contract
alone - which is exactly what U10 refused to do and why this was still open to settle.

### A count in prose is not the set

`approval.py:181-190`'s docstring says *"These **three** values"* and declares **four**. Harmless
today and exactly the shape that decays: `r7-fixes` fixed two stale counts in a docstring this same
week ("these seven" was six, "the two sets" was four). **Whoever applies this ADR fixes the count and
should prefer prose that does not carry one** - "the values below" cannot go stale.

## What this ADR does not settle

**Not `ApprovalState`'s relationship to `ApprovalDecision.approved`.** The boolean and the state are
computed together and could in principle disagree; nothing asserts they cannot. That is a separate
question about an invariant, not about a vocabulary, and folding it in here would be the mistake
ADR-0021 named.
