# SCAN-BOUND - ADR-0024 is Accepted and 513 unreviewed lines already exist

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `scan-bound`. Your branch is `feat/scan-bound`. Your report goes to
`docs/worklogs/SCAN-BOUND-REPORT.md`, committed on your branch. Your task record is **#74**.

## The situation, and the part that should make you careful

**ADR-0024 is Accepted** (ruling at the bottom of `docs/adr/0024-*.md`, 2026-08-29). Read the ADR AND
the ruling - the ruling corrects the ADR's own text on one point.

**An implementation already exists on `rescue/adr-0024-scan-bound` and you must not trust it.** 513
insertions: the client change, 331 lines of tests, a harness row, and an untracked
`scripts/probe-scan-bounds.py`. It was written by an agent that **never reported it**, found
uncommitted in a worktree during a cleanup that would have destroyed it. **Nobody has reviewed a line
of it and its numbers have never been re-measured.**

Treat it as a strong hint about shape and as evidence of nothing. **Re-measure everything you keep.**

## What the ADR decided

Two mechanisms, and neither is a substitute for the other:

1. **A zero-progress break.** A FULL page adding nothing to `seen` and nothing to `unidentified`
   breaks and sets `incomplete = True`. This cannot fire on healthy paging.
2. **A ceiling, IN RECORDS.** Reaching it sets `incomplete` and logs.

**The ceiling is in RECORDS, not pages, and the ruling explains why the ADR's own `MAX_PAGES` text is
wrong:** the ADR requires any bound to be *"sane at both 50 and 500 records per page"*, and a page
ceiling is a different record count at each page size - which is the objection the ADR itself raises.
The rescued branch already chose records. That choice is right; verify the implementation of it.

## Where the code is

`src/fast_mcp_jobvite/services/jobvite_client.py`, the loop at `:2037`. Its only exits today are a
short page and the non-exhaustive caller cap - **there is no bound on the exhaustive path**, which is
the defect.

`scan()` still has **zero callers in `src/`**: both grep hits are comments saying so
(`tools/jobs.py:321` and `:680`). Re-check that yourself; if a caller has appeared since, the
consequences stop being latent and your report should say so loudly.

## The probe is the most valuable thing on that branch

`scripts/probe-scan-bounds.py` runs both failure directions:

- **NON-ADVANCING** - ignores `start`, answers the same full page forever. This is R5's fake.
- **ADVANCING-FOREVER** - honours `start`, answers a full page of NEW records forever. **R5's fake
  cannot produce this**, and it is why the ADR says the ceiling and the zero-progress break are not
  substitutes.

It reports, per arm, which bound fired, after how many requests, and **what the caller ends up
holding** - because a bound returning `incomplete=True` and a bound raising a 503 are both "bounded"
and are not the same answer.

Its recorded pre-fix numbers, which you must RE-MEASURE rather than quote:

```
A1  budget 60s   requests issued: 2001   *** UNBOUNDED ***
A2  budget  2s   requests issued: 2001   *** UNBOUNDED ***
```

**Commit the probe and make it gate**, the way `docs/reviews/probe-r6-breaker-reset.py` was made to
gate at `3ef01f5`: every arm's verdict derived from the same predicate the gate uses, so the line a
human reads and the exit code a machine reads cannot disagree. That probe printed `not counted (ok)`
beside a failing counter for exactly that reason and the gate caught what the prose did not.

## What must not happen

- **Do not let the outbound budget be the answer.** The ADR's load-bearing point is that the budget
  bounds a symptom in wall-clock only: the scan still makes every request it can afford, learns
  nothing, and reports a timeout rather than "the server is not advancing". A budget-only fix is a
  rejected design.
- **Do not terminate on `total`.** `DESIGN.md:486-487` forbids it and the ADR does not weaken that.
- **Do not pick the ceiling to make a test pass.** Say what number you chose, why, and what it costs
  at 50 and at 500 records per page. The ADR requires it be sane at both.
- **`incomplete` must be observable by the caller.** A bound that silently truncates is worse than
  the unbounded loop, because it answers confidently with a partial result.

## Gates

Suite and anchor floors DERIVED from `ci.yml` by grep, never retyped - branch-local floors have been
wrong here four times. 0 skips. Full gate before folding, not after. Your harness rows need a
**derived** ROW_FLOOR: run the harness, read its own count from its own output. `ci.yml` is the
orchestrator's - put the steps you need in your report.

A mutation harness owns the working tree for its whole run: one at a time, never under a `timeout`
short enough to fire, and do not read the tree or commit while one runs.

## In the report

What you kept from the rescue branch and what you rewrote, with the measurement for each. Your own
probe numbers, before and after. The ceiling you chose and its cost at both page sizes. Then what you
could not settle - including whether the defect is reachable against real Jobvite, which needs an
endpoint that ignores `start` and for which no credential exists. R5 recorded that unsettled, the ADR
repeated it, and you almost certainly cannot close it either. Say so rather than implying otherwise.
