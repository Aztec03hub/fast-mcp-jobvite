# CODE-REVIEW-R5 - U6, which is merged and has never been reviewed

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `code-review-r5`. Your report goes to `docs/reviews/REVIEW-R5.md`, committed on
branch `review/r5`. **You are READ-ONLY on `src/`, `tests/` and `scripts/`.**

## Why this round exists

**U6 is merged at `8d7af64` and nobody has reviewed it.** 1957 lines: the paging block in
`services/jobvite_client.py`, `tests/test_pagination.py` (628 lines), and two new harnesses.

It was built carefully - 16/16 mutation, 10/10 amputation, zero vacuous - and **three of its own rows
failed first and all three were real defects in its own tests.** Its report is unusually honest, and
it deleted a branch it had written because it could not justify it from the design. **That is a
reason to review it, not a reason to skip it.** Every reviewed unit here has produced a High.

## Where to look first

`docs/worklogs/U6-IMPL-REPORT.md` ends with what it could NOT settle. **Start there**, and note that
one of its findings (F1) is already fixed at `8d7af64` and two are not.

- **F2 (open)**: `config.py:207` `pagination_start_base` is a scalar `int | None` where
  `DESIGN.md:478-480` requires per-resource, and `.env.example:101` calls it "per resource" while
  offering one value. The client already takes a `Mapping`. **The config and the template disagree
  with each other and with the design - decide which is wrong.**
- **F3 (open)**: two contracted citations in `config.py` that RESOLVE and are wrong at both ends.
- **The wire page size.** `min(transport_cap, configured_result_cap)` with no branch, so an
  exhaustive scan pages at 50: 25 requests for 1,240 records against a 6/min self-throttle. This is
  deliberately deferred to U7 by my decision, because the outbound budget determines whether that is
  permissible. **Not a finding that it is unresolved. A finding about the CONSEQUENCE is welcome.**
- **`DEFAULT_ID_KEY` is `eId` and the only recorded success body is the CANDIDATE one**
  (`JOBVITE-API.md:395-400`). A wrong key makes every record `unidentified` - kept, never
  de-duplicated, silently immune to the seen set. **Check what happens on that path**; the fixture is
  the assumption, so no existing test can contradict it.

## The claims most worth attacking

U6 makes three that the whole unit rests on. Test each rather than reading it:

1. **"De-duplication defends against OVER-reading only."** `DESIGN.md:465-468` says it cannot recover
   a record never returned, *"which is exactly why the fix is starting at 0 rather than
   de-duplicating harder."* U6 says it wrote a test proving the LIMITATION. **Does that test actually
   prove it, or does it only demonstrate duplicates being dropped?** The difference decides whether a
   future author concludes the seen set is the safety mechanism and moves the start.
2. **"Termination is on a SHORT page and never on `total`."** Find the path where a lying `total`
   could still shorten or extend the loop.
3. **"The completeness check is armed ONLY by an exhaustive scan."** U6's own M9 row initially
   SURVIVED because its arm-two case was a capped call that FILLS its limit and so never reaches a
   short page - `not exhaustive` was doing nothing. It fixed that. **Look for the same shape
   elsewhere**: a condition whose test never reaches the branch it guards.

## The shapes that have produced findings here

Hunt these before reading for style. Each has produced a real finding on this project.

1. **A control that is not wired.** U6's two harnesses are wired (`8d7af64`) - verify that, do not
   assume it. For every other checker or assertion U6 added, find the thing that RUNS it.
2. **A green that tested nothing** - a skip, a selection matching nothing, an assertion passing
   against an absent file, a grep at a path that does not exist.
3. **A test NAME is an unverified claim about its BODY.**
4. **A hand-kept list beside the container it describes.** SEVEN instances here. Does the paging code
   enumerate anything the code already knows?
5. **The positive control depends on the defect.**
6. **Fail-closed on error still fails OPEN on empty.** Paging is full of empties: a zero-item page, a
   `None` total, an envelope with no items key. **What does each one do?**
7. **A constant that a test reads the same way the code does**, so an assertion moves with the value
   it is meant to pin. U6 found one of these itself (M8) - look for siblings.

## What is already known, so you do not re-derive it

- **F1 is FIXED at `8d7af64`** and has a test whose whole point is `client_factory=None`, proved able
  to fail by amputation. A finding that it is open is wrong; a finding that the fix or its test is
  inadequate is not.
- **500 and 1000 are UNOBSERVED as server limits** and are labelled as such at the constants and in
  the case that pins them. The label IS the handling. A finding that they are unverified is already
  known; a finding that the label is wrong or missing somewhere is not.
- **`start` being 1-based is a VENDOR CLAIM, not an observation.** What is observed is only that
  `start=0` is accepted and returns records, in one genuine 200. C3-I1 and C6-D1 stay
  `unmitigated (B15)`. Do not re-file that; do flag anywhere the code or a comment upgrades it.

## What you may not do

- **No edits to `src/`, `tests/` or `scripts/`.** `r2-fixes` is live in `src/` and `tests/`, and
  `u7-resilience` is live in `services/jobvite_client.py` - **the very file you are reviewing.**
  Review the merged state at `8d7af64`, cite against it, and expect the working tree to move under
  you. Use `git show 8d7af64:<path>` rather than reading the working tree, and say so in your report.
- **`docs/DESIGN.md` is FROZEN** at `c15b138`. Read it as `git show c15b138:docs/DESIGN.md`. A defect
  there is a **Proposed** ADR in your report, never an edit.

## Every finding ships with a suggested fix

At every severity, nits included. Rank by severity, cite `file:line` from `grep -n` or a numbered
read, and state the failure each produces. **A surviving mutation is the strongest finding you can
bring me** - you may run the existing harnesses read-only, but see the isolation note: pin
`8d7af64`, do not mutate a tree another agent is editing.

**End with what you did NOT verify**, and keep that for what you could not settle rather than what
you did not try. A cheap item parked there reads as rigour and is not.
