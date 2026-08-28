# ADR-0016: `astral-sh/setup-uv@v5`, where the standard pins `@v4`

**Status:** Accepted
**Type:** Deviation

## Context

`devops/ci-cd.md:173` pins `astral-sh/setup-uv@v4`, and `COMPLIANCE-SPEC.md:136` copies that pin
into this project's obligations with the instruction that the versions be copied exactly. This
repository uses **`@v5`**.

The drift was found by the COMPLIANCE-SPEC pass, and **what made it worth a finding was its
direction, not its existence**: `actions/checkout` was pinned `@v4` where the standard says `@v6`,
and `setup-uv` `@v5` where the standard says `@v4`. **One behind, one ahead** — which is the
signature of pins written from habit rather than copied from the standard, and it is why both were
looked at rather than one.

`actions/checkout` has been corrected to `@v6`. This ADR is about the other one.

## Decision

**Stay on `astral-sh/setup-uv@v5`.**

## Why not simply comply

Complying means **downgrading a CI action by a major version to match a document**. That is the
wrong direction for three reasons, and the third is the one that decides it:

1. **A newer major of a setup action is not a defect to be corrected.** The standard's `@v4` is a
   snapshot of what was current when `ci-cd.md` was written. Nothing in the clause argues for `v4`
   specifically; it is a pin, not a rationale.
2. **Downgrading changes behaviour in a way nobody has tested here.** `v5` is what this
   repository's CI was written against and what its cache and Python-resolution steps assume. A
   downgrade to satisfy a document would be an untested change made for a documentary reason —
   precisely the shape this project has rejected elsewhere.
3. **The security argument runs the other way.** This project already corrected
   `trufflesecurity/trufflehog@main` to a release tag because a moving reference is untrustworthy
   third-party code. The same reasoning does not then support pinning *backwards* to an older major
   of a different action. **A pin exists to make the version deliberate, not to make it old.**

## What this ADR does not claim

**It does not claim `v5` is better.** Nobody here has compared them. The claim is narrower: the
standard's pin is a dated snapshot, no clause argues for `v4` on its merits, and moving backwards
across a major version to satisfy a document is a change with real behavioural risk and no stated
benefit.

**It does not generalise to other pins.** `actions/checkout` was *behind* the standard and has been
brought forward, because there the standard was ahead and being behind had no argument either.
**The rule this ADR follows is "match the standard unless moving to match it is itself a
regression", not "our pins are fine".**

## Consequences

- **`COMPLIANCE-SPEC.md:136` and `ci-cd.md:173` now disagree with the tree, deliberately**, and this
  ADR is the record. A future compliance sweep will flag it again; it should find this file and
  stop, which is the whole purpose of writing it down rather than leaving a comment in a workflow.
- **The standards corpus should be told.** `ci-cd.md:173`'s pin is stale, and the right long-term
  fix is a defect raised against that document rather than sixteen repositories each carrying an
  ADR. That is out of scope here and is not done.
- **`actions/setup-python@v5` is unaffected** — the standard does not pin it at all, so there is no
  deviation to record.
