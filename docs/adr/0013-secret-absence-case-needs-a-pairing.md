# ADR-0013: §8's secret-absence case needs a positive pairing, as the audit cases have

**Status:** Accepted
**Type:** Design change

> **Accepted and APPLIED**, with ADR-0012, in the ADR batch. The design edit was held until the
> implementation plan settled, because the plan repoints its citations against the frozen
> `DESIGN.md` object. It never blocked a unit: U3 could implement the pairing as a plan decision,
> and what this ADR settled is that §8 says so.

## Context

§8 case **#2** (`DESIGN.md:1223`) reads, in full:

> *"a secret never reaching a log record, including the `jobFeed` URL;"*

It asserts an **absence**. Nothing in it establishes that the log stream it is absent from contains
anything at all. **A server that emits no log records passes it perfectly.**

The design already knows this shape is unsafe, and says so, twelve lines below, about a different
pair. Case **#4** asserts the audit event is emitted and carries its mandated fields, and
`:1229-1231` explains why:

> *"**This case is positive on purpose.** The PII case below asserts an absence, and an absence
> passes trivially against a server that emits no audit event at all; the two are paired so that
> neither can be satisfied by silence."*

**That reasoning is exactly as true of #2 and the log stream as it is of #4/#5 and the audit
stream.** #4 does not supply the pairing, because it is about a different stream: an audit event
existing says nothing about whether a log record was written.

The exposure #2 guards is not minor. It covers `C5-I1` (`:1725`), rated **High** — the `/v1/jobFeed`
URL structurally carries `sc=` as a query parameter, so redaction is the only thing standing between
a secret and a log line.

## Decision

§8 gains a positive pairing for the log stream, and #2 is rewritten to name it, on the same
construction the design already uses at `:1229-1231`.

The pairing asserts that the log stream **carries records for an invocation that produced them** —
so that #2's absence is measured against a stream proven non-empty, rather than against silence.

## Why this belongs in the design and not only in the plan

The implementation plan can, and does, carry the pairing as a plan decision for U3. That is enough
to *implement* it. It is not enough to *keep* it, for two reasons:

1. **§8 is what the three gates read and what every later reader reads.** A plan paragraph is
   invisible to `check-coupling.py`, to the controls harness, and to the sweep. The plan established
   this itself when it found that a §8 case with no §11 row is invisible to the gate — the same
   argument applies to a pairing that exists only in a plan.
2. **It already failed to propagate once, which is the evidence rather than the theory.** A plan
   review found that after the pairing was written into U3's prose, **`C5-I1`'s arm in U12 remained
   an absence over the same log stream, guarding the same secret, one unit later.** The plan-level
   fix predicted against itself: the rule lived in one unit and did not reach its sibling.

**A construction stated in §8 is inherited by every case; a construction stated in a plan is
inherited by whoever reads that paragraph.**

## Scope, stated because a narrower ADR would miss half of it

This ADR covers **both** instances of the shape:

- **#2** in §8, the general secret-absence case, and
- **`C5-I1`'s arm in U12** — the `jobFeed` URL specifically, which is where the same defect recurred
  after the first was fixed.

An ADR written only against #2 would leave the second one to be rediscovered, which is the exact
sibling failure that produced it.

## Consequences

- **One more required case in §8.** The count is not stated anywhere in the design, deliberately —
  §11's "the table is the count" rule generalised — so nothing goes stale by adding it.
- **The gate gains purchase on it** once a §11 row names it, and does not before. GATE-2 requires a
  case to cite its owner; that is a weaker property than a row naming it, and the design says so at
  §8's SIGTERM bullet. This case will be named by `C5-I1`, which is a row, so it gets the stronger
  property.
- **No rating changes.** `C5-I1` stays High. This strengthens the test behind an existing
  mitigation; it does not alter the mitigation or the exposure.
- **U3 and U12 are unaffected in scheduling.** Both implement the pairing regardless; the ADR
  decides where the construction is recorded, not whether it is built.

## What this ADR does not settle

Whether the positive pairing is its own case or an added arm on an existing one is left to whoever
applies the edit. The design's own precedent at `:1229-1231` is a *pair of separate cases* rather
than a two-armed one, which is the weaker argument for separateness — precedent rather than reason —
and is recorded as such rather than dressed up.
