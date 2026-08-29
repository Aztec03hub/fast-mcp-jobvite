# ADR-0020: The 30-day advisory budget runs from the recorded date, not from now

**Status:** Accepted
**Type:** Deviation

> **Accepted, not Proposed.** This changes no `DESIGN.md` text. It records which of two readings of
> an ambiguous clause the shipped code implements, and why. Nothing is waiting on it.

## Context

`DESIGN.md:1510-1515` requires that a time-boxed advisory ignore carry *"the advisory id, the date,
the reason it is unreachable, and **an expiry date no more than 30 days out**."*

**It does not say what the 30 days run FROM.** Two readings are available and they are not
equivalent:

- **From the entry's recorded `date`** - the ignore may live at most 30 days from the day someone
  decided it was unreachable.
- **From now** - the expiry may be at most 30 days beyond whatever day the check happens to run.

U11 had to pick one to build `scripts/check_advisories.py` at all, and picked the first. **It
reported the ambiguity rather than resolving it silently**, and this ADR is the record that was
otherwise going to exist only in a commit message and a test name.

## Decision

**The budget is measured from the entry's recorded `date`.**

Pinned by `test_the_30_day_budget_is_measured_from_the_recorded_date_not_from_now`, and by
`MAX_IGNORE_DAYS` being exercised at exactly 30 and exactly 31 days with both boundary controls
firing.

## Why, and the reason is not a preference

**Measured from now, the budget refills on every CI run.** An entry recorded on day 0 with an expiry
30 days out is legal on day 0. On day 20 it is still within 30 days of *now*, so it is still legal.
On day 100 the same entry is still legal, because "no more than 30 days out" is re-evaluated against
a clock that keeps moving. **The entry never expires and the mechanism never fires.**

That is precisely the drift the expiry exists to stop. `DESIGN.md:1515` says so in the same sentence:
*"exits non-zero on any expired entry, **so the ignore cannot outlive its justification by
drifting**."* A reading under which nothing ever expires cannot be the reading that clause intends,
so the ambiguity resolves on the design's own stated purpose rather than on taste.

## Consequences

- **An entry recorded more than 30 days ago is rejected even if its expiry is in the future.** That
  is the intended behaviour and it is the sharp edge: someone renewing an ignore must update the
  `date`, which means re-deciding that the advisory is still unreachable. **Re-deciding is the
  point.** Bumping only the expiry would be the drift.
- **The clock is injected, never read inside the check.** `check_entries(entries, now)` takes `now`
  as an argument and the CLI exposes `--now ISO-DATE`, so every boundary in the test module is a
  literal on both sides. A test that computes "30 days from now" against a fixture written at
  runtime passes on any implementation, which is the failure this avoids.
- **If the other reading is ever preferred, the change is small and the test names it.** Change
  `test_the_30_day_budget_is_measured_from_the_recorded_date_not_from_now` and the comparison it
  pins. This ADR is then superseded rather than quietly contradicted.

## What this ADR does not settle

**Whether `pip-audit` accepts `--ignore-vuln <id>` repeated per advisory.** U11 flagged this as its
biggest unverified item and it remains open. That string comes from `DESIGN.md` and the
implementation plan, both of which assert it; **neither is the tool.** `pip-audit` is not installed
here, and installing it is the dependency addition the serialised slot forbade at the time.

**If the design is wrong about the interface, all 33 tests still pass and the flags are still
wrong** - the tests assert that the flags this project decided on are emitted, not that `pip-audit`
understands them. That resolves the moment task #26 puts `pip-audit` in the lock and a real
invocation consumes the output.

**And nothing consumes those flags today.** The ignore mechanism is fully built and connected to
nothing, because no CI step runs `pip-audit` at all. That is a separate defect, tracked as #26, and
this ADR does not close it.
