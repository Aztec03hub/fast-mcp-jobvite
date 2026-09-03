# Ruling on U6-F2 / R5-L1: the scalar start base is a deviation, not a style choice

**Decided 2026-08-29 by the orchestrator.** U6 raised it, R5 re-confirmed it open and recommended
the opposite of what I am deciding, so the reasoning is written out rather than asserted.

## The disagreement, stated fairly

`config.py:207` is `pagination_start_base: int | None = None` - one integer. R5-L1 recommends
**keeping the scalar**, expanding it to every route at the call site, and correcting `.env.example`
to say "global". Its argument is good and I am not dismissing it:

> Since no reader exists, either option is a green-field change rather than a contract break, and
> (b) ... is the one I would take. It is smaller, and it cannot express the thing the design warns
> against (a per-route 1 written down as the vendor's claim) any more dangerously than the mapping
> can.

**Both halves of that are true.** M1 established that `pagination_start_base` reaches nothing, so
nothing breaks either way, and a scalar genuinely is a smaller change.

## Why I am deciding the other way

`git show c15b138:docs/DESIGN.md`, 478-480:

> - The base is **per-resource, not global**. `/v1/jobFeed` is `[OFFICIAL]` 1-based; the v2
>   resources are `[INFERRED]`. **They are configured separately.**
> - `JOBVITE_PAGINATION_START_BASE` **overrides per resource** for anyone who has established the
>   truth.

**A scalar cannot express that.** So the choice is not between two shapes of a setting - it is
between implementing the frozen design and departing from it.

**"Smaller" is not the axis.** A smaller change that contradicts a frozen document is not a smaller
change; it is an **unrecorded deviation**, and this project's whole freeze discipline exists to stop
exactly that. Option (b) is legitimate, but only as a numbered ADR that says "the design specifies
per-resource; we ship global; here is why." Nobody has written that ADR, and R5 did not propose one -
it proposed the edit.

So:

- **Option (a), per-resource, is COMPLIANCE and needs no ADR.**
- **Option (b), the scalar, is a DESIGN CHANGE and needs one.**

That asymmetry is the whole decision, and it survives the fact that R5's engineering judgement about
which is nicer may well be better than mine.

## The decision

**Take (a).** Parse `JOBVITE_PAGINATION_START_BASE` as `resource=base` pairs into the `Mapping` the
client already accepts. Three reasons, in order:

1. **It is what the frozen design says**, and no ADR says otherwise.
2. **The client is already built for it.** `JobviteClient.__init__` takes
   `start_base_overrides: Mapping[str, int] | None`, so (a) is a config-side change only - the
   asymmetry R5 noticed cuts toward (a), not away from it.
3. **The design's reason is specific and survives M1.** `/v1/jobFeed` is `[OFFICIAL]` 1-based and the
   v2 resources are `[INFERRED]`. Those are different epistemic states about different routes, and a
   single number forces one answer onto both. That is the same "one value standing in for two
   different things" defect the result cap produced in F1.

## What this ruling does NOT decide, and it matters

**Not that R5 was wrong to recommend (b).** It weighed size and risk and reported its preference with
its reasoning - which is what a reviewer should do. What it did not weigh is the freeze, and that is
the orchestrator's job rather than a reviewer's.

**Not that the scalar is unsafe.** R5's point that neither shape can express a per-route `1` "any
more dangerously" than the other is correct. The objection is procedural, not safety-based, and
saying so keeps the ruling honest.

**Not the timing.** `config.py` is `r2-fixes`' file right now, so the edit waits. This ruling exists
so that whoever applies it is not re-litigating the choice at the keyboard.

## What must land together

- `config.py`'s parse, and a validator that refuses a malformed pair rather than silently ignoring it
  - **fail-closed on error still fails OPEN on empty**, so an empty value must mean "no overrides"
  and a *malformed* one must refuse at boot, matching every other refusal in that file.
- `tools/jobs.py` passing `start_base_overrides` through - **R5-M1, and the two are one change**:
  wiring a parser to a factory that drops it reproduces M1 exactly.
- `.env.example:101`'s comment, which today says "per resource" beside a single value. **It is the
  only one of the three that is already correct about intent** and wrong only about the shape it
  offers.
- A test that fails if the override is dropped, modelled on F1's - `client_factory=None` is what
  makes that case able to fail at all.
