# BRIEF #209 (R21-H1): the gate's own re-derivation recipe has no left boundary

Read `docs/briefs/PREAMBLE.md` IN FULL first. It is the canon; this file is only the work.

**Worktree:** your own, off `d2159e7` (main). Branch `fix/209-recipe-left-edge`. Do NOT touch the
shared checkout at `/home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite`.
**Read the finding first:** `git show 1045edb:docs/reviews/REVIEW-R21.md` (branch `review/r21`).

## The finding, as `review-r21` measured it

`docs/reviews/check-brief-report-references.py:83-86` carries a recipe headed "re-derive the
population WITHOUT TRUSTING THIS FILE". That recipe's regex has **no left boundary**, so it
returns the truncated phantom name that commit `1985471` RETRACTED as a published false finding.
Measured: recipe yields 23 names, the gate's own `REF` yields 22, and the difference is exactly
that phantom.

**The part that makes this a High rather than a nit:** the comment forty lines below, at
`:117-126`, records that phantom as a PUBLISHED FALSE FINDING and calls it load-bearing. So the
file documents the exact defect its own recipe reproduces.

**And it is one edge of two.** The same hunk in this population FIXED the recipe's DIRECTORY edge
(`docs/briefs/*.md` -> `docs/briefs`, with three new lines of prose about why a narrower
re-derivation is dangerous) and left the LEFT edge loose. A fix that repairs one edge of a
two-edge selector is the class this project keeps hitting.

## Suggested fixes - THE REVIEWER'S SUGGESTION, NOT AN INSTRUCTION

`review-r21` suggested: `grep -P` not `-E` (the lookbehind needs PCRE); better, give the checker a
`--list-names` flag so the recipe prints the GATE'S OWN population instead of re-implementing it.

**Verify the suggestion is sufficient before you adopt it.** Prescribed remedies from reviewers
have been measured WRONG on this project repeatedly, and at least three fixes here have rebuilt
their own defect one column over. State the defect as a PROPERTY, then check that your fix AND its
controls hold that property.

The `--list-names` route is the one I lean toward, because it deletes the second implementation
rather than repairing it - a recipe that cannot disagree with the gate cannot drift from it. If
you take it, say what the recipe is still FOR once it no longer re-derives anything independently:
if the answer is "nothing", that is a finding, not a detail.

## Deliverable

1. The fix, committed, with an arm in `docs/reviews/check-brief-report-refs-controls.sh` that
   FAILS on the pre-fix code and passes after. Update `ROW_FLOOR` to the new exact row count -
   the floor must EQUAL the live count, never bound it.
2. Proof in both directions, exit codes read on their OWN LINE. No `&& echo OK` anywhere: under
   `set -e` only the LAST command of an AND-list triggers errexit, and that shape has hidden a
   ruff red on this project.
3. `git merge --ff-only` command for me in your report.

## Where I think I am wrong

- I have NOT re-run the 23-vs-22 measurement myself. Re-derive it; if it does not reproduce, that
  is the report, and say so loudly rather than working around it.
- I do not know whether `grep -P` is available in the CI image. Check before you depend on it.
