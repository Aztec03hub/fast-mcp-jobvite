# BRIEF #212 (R21-M2): the fix for a COUNT finding restates a census that is short by one

Read `docs/briefs/PREAMBLE.md` IN FULL first. It is the canon; this file is only the work.

**Worktree:** your own, off `d2159e7` (main). Branch `fix/212-census-short-by-one`.
**Read the finding first:** `git show 1045edb:docs/reviews/REVIEW-R21.md` (branch `review/r21`).

## The finding

`2514990` fixed R20-M2 - itself a finding about a COUNT - and in doing so restated `e3b5c97`'s
census as **four kinds totalling 33**. Measured at that blob: **34 ADR files, 34 `Type:` lines,
FIVE kinds.** The missing row is `Correction to a count that is false about its own subject` -
**ADR-0034's own row**, the very file `e3b5c97` was adding.

`e3b5c97`'s commit message made the same omission and `2514990` copied it forward. `review-r21`
calls this the fifth count with a moved edge in this population.

The site is in `docs/adr/0034-the-adr-count-in-design-md-is-deleted-not-corrected.md` - the
paragraph beginning "THIS TABLE IS NOT THE ACCEPTANCE CENSUS AND SAID IT WAS."

## What makes this the interesting one

This is a fix for a count defect that shipped a count defect, in the ADR that RULES that counts
are deleted rather than corrected, and the omitted row is that ADR's own. Before you write
anything, decide which remedy the ADR's own ruling demands:

- correcting 33 -> 34 and four kinds -> five is the remedy the ADR forbids everywhere else;
- deleting the census and pointing at the command
  (`grep -h '^\*\*Type:\*\*' docs/adr/[0-9]*.md | sort | uniq -c`, run at the named blob) is the
  remedy it prescribes - but this census is EVIDENCE for a past ruling, dated and provenanced, and
  this project separately rules that a DATED RECORD is not a live count.

**Those two rules point opposite ways here and that tension IS the task.** Pick one, argue it from
the two rules by name, and write the reasoning into the document so the next reader does not have
to re-derive it. Do not split the difference silently.

## Deliverable

The fix, committed, gates green with exit codes read on their OWN LINE. `docs/DESIGN.md` must NOT
move - this is an ADR body, not the frozen design - but run `check-design-freeze.py` and confirm.
Then the `git merge --ff-only` command for me.

## Where I think I am wrong

- I have NOT verified "34 files, 34 Type lines, five kinds" at `e3b5c97` myself. Derive it at the
  blob (`git show e3b5c97:...`), not at HEAD - the whole defect is a figure read at the wrong
  moment, and re-measuring at the wrong moment would reproduce it.
- I am not certain the fifth kind's exact spelling is what I wrote above. Read it.
