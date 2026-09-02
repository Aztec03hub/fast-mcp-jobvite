# ADR-0019: `DESIGN.md:603` cites `§5.4`, and there is no §5.4

**Status:** Accepted
**Type:** Design change

> **Accepted and APPLIED**, in the ADR batch. It was the smallest change any ADR here proposed and
> it was still an ADR, because the alternative is an unrecorded edit to a frozen document - which
> is the precedent that matters, not the character count. `check-cross-references.py` went green on
> it and is now wired into `ci.yml`.

## Context

Found by **building U3**, not by reading. `DESIGN.md:603` reads:

> *"line carries the URL, because the v1 `jobFeed` URL is itself a secret (**§5.4**) and a retry
> line is..."*

**§5 has no subsection 5.4.** Verified against the frozen object `git show 135c3ac:docs/DESIGN.md`:

| Heading | Line |
|---|---|
| `## 5. Errors, logging, and correlation` | 485 |
| `### 5.1 The error contract` | 487 |
| `### 5.2 `problem+json` and the transport` | 555 |
| `### 5.3 Audit logging and `request_id`` | 567 |
| `## 6. Untrusted and sensitive content` | 714 |

Section 5 ends at `:714` with §6. The pointer resolves to nothing.

**The claim it points at is real and lives elsewhere.** *"The v1 `jobFeed` URL is itself a secret"*
is stated in **§4.1 Authentication, and three credential classes** (`## 4` at `:302`, `### 4.1` at
`:304`), at `:306-310`:

> *"`GET /v1/jobFeed` is the exception: it structurally requires `api`, `sc` and `companyId` as
> query parameters. Its URL is classified sensitive - never logged whole, never in an exception
> message..."*

## Decision

**`DESIGN.md:603`'s `(§5.4)` becomes `(§4.1)`.**

Nothing else changes. No behaviour, no threat row, no verification case.

## Why this is an ADR and not a typo fix

Because `DESIGN.md` is frozen, and **the value of the freeze is that it holds for changes this small
as well as for large ones**. An unrecorded "obviously fine" edit to a frozen document is how a freeze
stops meaning anything, and the next such edit is not obviously fine.

There is also a specific reason not to trust the "obviously fine" instinct here. **This project has
already produced wrong-subject citations repeatedly - they are enumerated in
`docs/reviews/WRONG-SUBJECT-REGISTER.md`, and the count is derived there rather than asserted
here.** A citation being wrong is exactly the kind of error that gets propagated by someone
correcting it quickly.

## What was checked, so the fix is not itself a guess

- **The section list was read from the frozen object**, not from the working tree.
- **The target was verified by SUBJECT**, not by line arithmetic: `:306-310` was read and it makes
  the claim `DESIGN.md:603` attributes to `§5.4`.
- **Siblings were swept.** `grep -n '5\.4'` over the frozen `DESIGN.md` returns **one** hit, the one
  above. So this is a single instance, not a pattern in that document.
- **A near-miss was excluded.** `docs/research/COMPLIANCE-SPEC.md` refers to *"§5.4"* three times
  (`:443`, `:501`, `:631`), and those are **correct** - that document has its own
  `### 5.4 A trap worth more than the rest of this section` at `:466`. They are references to its own
  numbering and must not be swept up in this fix. **This is the check that would have turned a
  one-line correction into three wrong ones.**

## Consequences

- **One character range in one line of `DESIGN.md` changes.** Apply it with ADR-0012, 0013, 0014 and
  0017 in the single commit those are waiting for, rather than reopening the frozen file five times.
- **No threat-model row moves**, no §8 case moves, and no gate output changes. `check-coupling.py`
  does not parse cross-references, so it neither caught this nor will notice the fix.

## The population IS now measured, and it is one

An earlier draft of this ADR ended by saying the population was unmeasured and that a validator
"would be a small script". It was, so it is written: **`docs/reviews/check-cross-references.py`**.

**492 `§n.m` references across `DESIGN.md`, `IMPLEMENTATION-PLAN.md` and `COMPLIANCE-SPEC.md`.
Exactly one does not resolve, and it is this one.** The script converges on precisely what an
implementer found by following a pointer.

**Getting there took two corrections, and both are worth recording because both produced findings
shaped exactly like real ones:**

1. **Judging each document against itself alone reported 30 unresolved references. 27 were the
   instrument.** `IMPLEMENTATION-PLAN.md` cites the design's sections constantly - *"the §7.4
   shutdown requirement"*, *"§11's threat rows"* - and every one of those resolves, in `DESIGN.md`.
   A plan is a plan FOR a design; its referent had to be declared.
2. **Of the nine that survived, eight were references to a NAMED THIRD DOCUMENT** - ``JOBVITE-API.md``
   §0.2, ``COMPLIANCE-SPEC.md`` §2.3, the spike's §20.2 - correct citations this checker cannot
   resolve because it does not read those files. A same-line filename now marks a reference
   external, and the two cases where the filename sits on a nearby line rather than the citing one
   are exempted individually, each with its reason recorded beside it.

**Had I reported after the first run, 27 of 30 findings would have been false**, and they would have
read exactly like the true one.

## What this ADR still does not settle

**Whether the eight external references resolve in their own documents.** The checker skips them
rather than following them; `FASTMCP-SPIKE-4.md` and `JOBVITE-API.md` are not in its target set.
"Correctly formed and pointing at a document I did not open" is weaker than "resolves".

**The gate IS wired, and this paragraph used to say it was not.** It was written before the ADR was
applied and said "not wired yet, deliberately" - correct at the time, and left standing after the
header of this same file recorded the opposite. `check-cross-references.py` runs at `ci.yml`'s
"Section cross-references resolve" step, which also refuses a run that found NO references at all,
because a checker that resolves nothing reports the same green as one that resolved everything.

The reasoning that paragraph carried is worth keeping, because it is the rule and not the status:
the gate was held back until it was green, since wiring a knowingly red gate trains everyone to
ignore it. That is the same discipline the W505 sweep followed, and the ShellCheck hook after it.
