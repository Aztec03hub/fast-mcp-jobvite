# CODE-REVIEW-R4 - U5, which is merged and has never been reviewed

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `code-review-r4`. Your report goes to `docs/reviews/REVIEW-R4.md`, committed on
branch `review/r4`. **You are READ-ONLY on `src/`, `tests/` and `scripts/`.**

## Why this round exists

**U5 is merged and nobody has reviewed it.** 3092 lines: `models/jobs.py`, `models/fencing.py`,
`tools/jobs.py`, `utils/constraints.py`, `tests/test_tools_jobs.py` (816 lines), the first
credentialed arm, and two new harnesses. It is the largest single unit in the repository and the
first one that makes the server do anything.

It was built carefully - 12/12 mutation, 11/11 amputation, and its own report is unusually honest
about limits. **That is a reason to review it, not a reason to skip it.** This project's rule is a
fresh reviewer every round, and the units that got reviewed produced a High each time.

## Where to look first

Its report, `docs/worklogs/U5-REPORT.md`, ends with what it did NOT verify. **Start there.** The
sharpest items, in its own words:

- **It never opened the TIER-1 standards.** Every standards clause in its comments is quoted from
  `DESIGN.md`'s citation of it, NOT verified against source. If a clause moved or was
  mis-transcribed, it propagated the error. `docs/reviews/check-clause-citations.py` now resolves the
  obligation map's clause column; U5's inline citations are a different population and are unchecked.
- **Item 7 is reported PARTIAL, not ticked**: it asserts the tool surface on both transport
  configurations but **binds no socket**, so "the server starts on HTTP" is over-reading its
  evidence. Decide whether that matters.
- **`ids` may or may not accept a comma-separated list** - the contract says unknown, and the tool
  documents a single id. A caller passing two would get one silently.
- **No date filter is offered**, deliberately, because the parameter names are `[ASSUMED]`. Check
  that the omission is complete: a partially-wired filter is worse than none.

## The shapes that have produced findings here

Hunt these before reading for style. Each has produced a real finding on this project, most more
than once.

1. **A control that is not wired.** Six instances. For every gate, harness and checker U5 added, find
   the thing that RUNS it.
2. **A green that tested nothing** - a skip, a selection that matched nothing, an assertion that
   passes against an absent file, a `grep` at a path that does not exist.
3. **A test NAME is an unverified claim about its BODY.** U5 found one itself: an assertion that read
   the same constant the mutation changed, so it moved with it. **Look for siblings of that.**
4. **A hand-kept list beside the container it describes.** SEVEN instances. `KNOWN_TOOLS` vs
   `TOOL_REQUIREMENTS`, `to_record` vs a dataclass, a README count vs the server. U5 adds a fencing
   registry and an allow-list in `_to_job` - **are they enumerations of something the code already
   knows?**
5. **The positive control depends on the defect.** A redaction test asserted `"jobvite.com" in detail`
   to prove it was not vacuous, so fixing the leak broke the control.
6. **Fail-closed on error still fails OPEN on empty.**

## What is already known, so you do not re-derive it

- `ids` is now in `NON_SENSITIVE_ARGUMENT_KEYS` (`fbaa971`) - deliberately, with the generic-name risk
  recorded in the file. Not a finding.
- The README's tool count is checked against a real `list_tools()` (`d7cf8c3`). Not a finding.
- The three structural limits are absent and recorded as absent (`efd0fef`). **The record is the
  fix**; a finding that they are missing is already known. A finding that the RECORD is wrong is not.

## What you may not do

- **No edits to `src/`, `tests/` or `scripts/`.** `harness-gates` is live in `scripts/` and `ci.yml`.
- **`docs/DESIGN.md` is FROZEN** at `c15b138`. Read it as `git show c15b138:docs/DESIGN.md`. A defect
  there is a **Proposed** ADR in your report, never an edit.

## Every finding ships with a suggested fix

At every severity, nits included. Rank by severity, cite `file:line` from `grep -n` or a numbered
read, and state the failure each produces. **A surviving mutation is the strongest finding you can
bring me** - you may run the existing harnesses read-only.

**End with what you did NOT verify**, and keep that for what you could not settle rather than what
you did not try.
