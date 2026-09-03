# Ruling: code review R1's lost findings are superseded by R3, and the backlog closes

**Decided 2026-08-29 by the orchestrator.** Task #4 has stood open since the R1 report was destroyed
with the scratchpad, holding eighteen findings that exist only as the sentence "I do not know what
they were". This settles it, because leaving it open costs a re-review that has already happened.

## What #4 asked for, in its own words

> **NEXT ACTION when someone picks this up:** do not try to remember them. Run a fresh review round
> against the units R1 covered and accept the duplication - a fresh reviewer is cheaper than a wrong
> reconstruction, and this project's rule is a fresh reviewer every round anyway.

## That round ran, and it is R3

`docs/briefs/CODE-REVIEW-R3.md:25` scopes R3 to **"Everything merged on `main`, which is seven units:
U0, U1, U2, U3, U4, U11, U15"**, plus `scripts/`, `docs/reviews/`, `ci.yml` and the suite. R1 ran
before R2, and R2 covered U1, U3 and U4 - so **R1's units are a subset of R3's**, and R3's scope is
strictly larger than what #4 asked to be re-covered.

R3 was also independent in the way #4 required. Its own opening states it:

> This is a **re-derivation, not a reconstruction**. I did not read task #4's summary of round 1
> before looking, and no finding below is carried over from it.

**The brief carved out exactly one thing** - `L6`, the missing suite-count floor - and L6 is the one
R1 finding that was not lost, because #4 recorded it and it was fixed at `79417d9`. Nothing else was
excluded, so no part of R1's surface went unlooked-at on a technicality.

## And R3's findings are closed

Nine findings: H1, M1, M2, L1-L5, N1. Eight were fixed and pushed (task #19); M2 was closed through
the harness-integrity work in task #20. R4 then covered U5, the only unit R3 predates. There is no
reviewed-but-unfixed remainder anywhere in the chain.

## What this ruling does NOT claim

**It does not claim R3 found R1's eighteen.** Two independent readers of one codebase do not produce
one list, and some of R1's findings are certainly not among R3's nine. The claim is narrower and is
the one #4 itself set as the bar: **the remedy R1's loss called for is a fresh independent round over
the same surface, and that round ran, reported, and was fixed.** Reconstructing beyond that would be
guessing at a document nobody can read, which #4 explicitly forbade.

If more findings remain in those units, the thing that will surface them is the next fresh round -
not this task, which carries no information a reviewer could act on.

**Task #4 is closed as superseded.** This file is now the record it said it was.
