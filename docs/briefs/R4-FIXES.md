# R4-FIXES - two Highs, five Mediums and three Lows on U5

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `r4-fixes`. Your branch is `fix/r4-findings`. Your report goes to
`docs/worklogs/R4-FIXES-REPORT.md`, committed on your branch.

## Read the report, not this brief, for the findings

`docs/reviews/REVIEW-R4.md` is merged on `main`. **Every finding ships a suggested fix and a
measurement.** Do not re-derive them; verify each against the current tree and then fix it.

**R4-H2 IS ALREADY FIXED** at `d08e5a6` - `SafeText` compiles, and `tests/test_constraints.py` is the
caller that was missing. Do not redo it. Everything else is yours.

## The two remaining Highs

- **R4-H1** - nothing asserts the outbound request, so `search_jobs`'s only argument can be deleted
  and the suite stays green. The reviewer proved it with `docs/reviews/probe-r4-unmutated-anchors.sh`,
  whole suite per row, restore checked with `cmp`. **The probe is committed - run it first**, and run
  it again after your fix so the report carries both numbers.
- **R4-H3** - the credentialed arm cannot detect the one thing it exists to detect. Its own docstring
  says it "converts the fixture from synthetic to recorded"; the reviewer found it cannot. Read what
  it claims, then decide whether the fix is the assertion or the claim.

## The trap in R4-M2, which is the one I most want handled carefully

**Ten inline `DESIGN.md` citations point at the wrong paragraph, consistently landing one paragraph
short.** A consistent off-by-one is a copied error, not ten independent slips.

- **Fix them by SUBJECT, never by adding a constant offset.** "They are all one short, so add one" is
  how a range contracts: it is right for the ten you checked and wrong for the first one that was
  already correct.
- **Cite from `git show c15b138:docs/DESIGN.md`**, the frozen SHA, never the working tree.
- This project has found nine wrong-subject citations before, four of them inside the ADR documenting
  that defect class. Assume the base rate is not zero for the ones R4 did NOT check.

## The rest

M1 (fencing registry rooted at a hand-named model), M3 (a mutation row whose test was renamed reports
KILLED forever), M4 (both U5 CI steps pass against a harness with zero rows), M5 (the amputation
harness reports the vacuous shape and gates on something else), L1 (`_to_job` is a hand-kept list
beside `Job`), L2 (`getattr(..., "meta", None)` turns a library rename into silent trace loss), L3,
N1.

**M3, M4 and M5 are all "the harness cannot fail" shapes** and belong together. Note `scripts/` now
has `check-harness-anchors.py`, which reads every anchor statically - use it, and if your fix changes
the anchor count, re-run `--self-check` and update `--floor` in `ci.yml`.

## Standing requirements

- **Every fix gets an amputation or a mutation that proves it can fail.** A fix for "the harness
  cannot fail" that is not itself proved able to fail is the same defect one layer up.
- **`docs/DESIGN.md` is FROZEN** at `c15b138`. A defect there is a **Proposed** ADR, never an edit.
- The suite floor in `ci.yml` fails if the count drops. If your work removes a test, say why.
- W505 is live at 72. Use `docs/reviews/b49b/reflow-doc-lines.py` rather than hand-wrapping - it
  preserves `#:` markers correctly as of `59f0a8b`.

## In the report

Per finding: what you measured before, what you changed, and the amputation proving it. **End with
what you could not settle** - and if you judge a finding wrong, say so with evidence rather than
fixing it to be safe.
