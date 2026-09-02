# RULING #231B: a range declaration does not cover a merge, and the gate ratchets rather than demands zero

**Ruled by the orchestrator, 2026-09-02.** This settles the half of `#231` left open at `5a4d4f2`.
Part A (the merge-authored PREAMBLE paragraph stays, with a provenance note) is already applied and
is not revisited here.

## The question, as `#231` posed it

> Should a whole-tree declaration be able to clear a merge the declarer demonstrably did not read?

## The evidence, re-measured before ruling rather than carried forward

`REVIEW-R21.md:3` declares `<!-- REVIEW-COVERS: c749334..80463a5 -->` with no `PATHS:` filter, and
that declaration is what clears merge `73dd717` in `check-review-coverage.py`. The same report then
said, of the four merges in its range, that *"`git show --cc` on all four produces an empty combined
diff ... no third version was invented at any merge."*

One command refutes it:

    git show --cc 73dd717 | wc -c        ->  11376

The combined diff carries a third version of `docs/briefs/BRIEF-199-ratchet-defects.md`, present in
neither parent. **R21 was right about two of the four** - `check-merge-invented.py` independently
reports `invented=0` for `b9b59dd` and `cd8c938` - and wrong about the universal that swept in the
other two. Its own §2 had already named `73dd717` as needing separate treatment, eighteen sections
above. The sentence is corrected in place in `REVIEW-R21.md`, because a reader reaches a coverage
green through it.

Population today, from the instrument rather than from a report:

    uv run --frozen python docs/reviews/check-merge-invented.py --range c749334..HEAD
    -> TOTAL merges=21 invented_lines=53

## Decision

**1. THE WHOLE-TREE FORM STAYS.** It is not the defect. Banning it would cost the reviewer who
genuinely did read the tree, and it would not stop a false `PATHS:` list either - a wrong narrow
declaration is just as unchecked as a wrong wide one. `review-r22` chose the narrow form and listed
what it had not read, which proves the instrument already supports the honest shape; nothing
required the wide one. **What was wrong here was an unchecked claim, not a syntax.**

**2. A RANGE DECLARATION DOES NOT COVER A MERGE'S INVENTED CONTENT.** This is a statement about what
a reviewer's reading physically contains, not a policy preference. A merge's third version appears
in no branch diff, in no `git log -p`, and in no per-commit review - it is visible only to `--cc`.
A reviewer who read the commits in `A..B` has therefore genuinely not seen it, whatever their
declaration says. Coverage over a range is a claim about the non-merge commits in that range;
merge-invented content needs its own acknowledgement.

**3. THE MECHANISM IS A SET-RATCHET OVER `(merge, path)` PAIRS, NEVER A DEMAND FOR ZERO.** This is
the shape `#222` named and the shape `#151` already proved on the review backlog: a set lets an
entry and a clearance cancel, where a count cannot and a zero-demand cannot. `check-merge-invented.py`
already carries `--strict` for this day, and **`--strict` as a zero-demand is REFUSED**: 53 invented
lines exist across 21 merges today and the checker's own wiring exemption says why - a reflow that
re-wraps a paragraph surfaces as many invented lines while the sentence is unchanged. A gate that
goes red on the first re-wrapped paragraph is red by construction, and this repository has measured
what happens next: 119 consecutive red mirror runs went unread because a switched-off gate and a
failing gate render identically.

## What this ruling deliberately does NOT do

**IT DOES NOT WRITE THE BASELINE, AND THAT IS THE POINT.** A ratchet's baseline is a claim that
someone read the population. 53 lines across 21 merges is measured; how many are reflow and how
many are content is **not**, and `#222` left 9 of its 10 flagged merges unexamined. **Writing a
baseline from an unread population records noise as debt and manufactures exactly the coverage this
ruling exists to refuse** - the finding rebuilt inside its own remedy, which has happened three
times tonight already. The rule is decided; the number waits for a reading.

**It does not wire the checker.** That follows the baseline, not this ruling, and
`check-checkers-are-wired.py` already records the checker as `UNWIRED_BY_DECISION` with the reason
above. That entry stays accurate.

**It does not re-open `#111`, `#203` or the record convention.** Those govern citations drifting in
a record. R21's sentence is not a drifted citation; it is a false measurement, and a false
measurement that a live gate resolves through gets corrected in place.

## What a reviewer must do from now on

Declare `PATHS:` unless the tree was genuinely read. If the range contains a merge, run

    git show --cc <merge> | wc -c

and say what you found. A zero there is a real result and cheap to produce. **A non-zero is not
automatically a defect** - reflow reads the same as invention to every instrument here, which is
why the threshold is open - but it is a thing you have to have looked at before your declaration
clears it.
