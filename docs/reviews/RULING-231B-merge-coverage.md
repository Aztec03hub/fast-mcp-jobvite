# RULING #231B: a range declaration does not cover a merge, and the gate ratchets

**Ruled by the orchestrator, 2026-09-02. Revised the same day after `review-231b`,** which attacked
the ground under Decision 2 exactly as it was asked to and broke it, and which found that the
command this ruling told reviewers to run cannot return the result it promised. Both are corrected
below and the corrections are the interesting part. This settles the half of `#231` left open at
`5a4d4f2`; Part A is applied and not revisited.

## The question, as `#231` posed it

> Should a whole-tree declaration be able to clear a merge the declarer demonstrably did not read?

## The evidence, re-measured before ruling and re-measured again after review

`REVIEW-R21.md:3` declares `<!-- REVIEW-COVERS: c749334..80463a5 -->` with no `PATHS:` filter, and
that declaration is what clears merge `73dd717` in `check-review-coverage.py`. **That mechanism is
run, not asserted:** `review-231b` deleted only line 3 from a COPY and fed it back through the
checker's own `--reviews` flag, and `73dd717` moved from covered to `NONE`, taking 22 commits with
it. The same report said, of the four merges in its range, that *"`git show --cc` on all four
produces an empty combined diff ... no third version was invented at any merge."*

**The combined diff of `73dd717` is 7226 bytes, and it carries a third version of
`docs/briefs/BRIEF-199-ratchet-defects.md` present in neither parent.**

    git show --cc --format= 73dd717 | wc -c     ->  7226

**THIS RULING FIRST PUBLISHED 11376, WHICH IS THE DIFF PLUS THE COMMIT MESSAGE.** 7226 is the
figure `check-merge-invented.py` prints as `cc=7226B` and the one `#222` recorded. The two look
4150 bytes apart and are the same finding measured through different instruments - which is the
defect this project keeps hitting, committed inside the ruling about it.

R21 was right about two of the four: the detector independently reports `invented=0` for `b9b59dd`
and `cd8c938`. Those verdicts are kept. Only the universal is removed.

## Decision

**1. THE WHOLE-TREE FORM STAYS.** It is not the defect. Banning it would cost the reviewer who
genuinely read the tree, and it would not stop a false `PATHS:` list either - a wrong narrow
declaration is exactly as unchecked as a wrong wide one. `review-r22` chose the narrow form AND
listed merge-invented content among what it had not verified, which proves the honest shape is
already available and nothing required the wide one. **What was wrong here was an unchecked claim,
not a syntax.**

**2. A RANGE DECLARATION DOES NOT COVER A MERGE'S INVENTED CONTENT, AND THIS IS A POLICY CHOICE
THAT THIS RULING MAKES.** The first version of this section called it *"a statement about what a
reviewer's reading physically contains, not a policy preference"*, on the ground that merge-invented
content is *"visible only to `--cc`"*. **That ground is false and was refuted by measurement:**

    git diff 73dd717^1 73dd717 -- docs/briefs/PREAMBLE.md   ->  26 lines, no flag
    git show 73dd717                                        ->  prints it; show DEFAULTS to --cc
    git log -p c749334..80463a5 -- docs/briefs/PREAMBLE.md  ->  0

Only the last is blind. Diffing a merge against its own mainline parent is ordinary reviewing and
prints every invented line, so whether a reviewer saw this content depends on **which command they
ran** - a practice, not a property of the content. Calling a policy a fact does not make it bind
harder; it makes the argument unfalsifiable, and this one was falsified in three commands.

**The ground that does hold, and it is enough: a declaration records the SPAN, never the COMMANDS.**
`REVIEW-COVERS: A..B` cannot distinguish a reviewer who ran `git show` on each merge from one who
ran `git log -p` over the range, and the second is blind. The declaration therefore cannot carry the
information that would justify clearing a merge, whatever the reviewer actually did. **So this
ruling requires the acknowledgement to be explicit** - not because the content is invisible, but
because the record cannot tell the two readers apart.

**3. THE MECHANISM IS A SET-RATCHET OVER `(merge, path)` PAIRS, NEVER A DEMAND FOR ZERO.** `#222`'s
shape and `#151`'s proved one: a set lets an entry and a clearance cancel, where a count cannot.
`check-merge-invented.py` already carries `--strict`, and **`--strict` as a zero-demand is REFUSED -
but only on forward-looking grounds, which is narrower than this ruling first claimed.** The first
version implied today's population is mostly reflow. `review-231b` measured it, which nobody had:

    122 invented lines, 13 reflow, 109 CONTENT  ->  10.7% reflow

**89% is genuine content, so the "it would go red on formatting" argument is false about today.**
What survives is the forward-looking form: a zero-demand goes red on the FIRST future re-wrap
whatever today's mix is, and this repository has measured what happens next - 119 consecutive red
mirror runs went unread, because a switched-off gate and a failing gate render identically.

## The population, and why the baseline is still not written

**THE FIRST VERSION NAMED THE WRONG CONTAINER.** It said 21 merges / 53 lines over
`c749334..HEAD`, which is R21's REVIEW RANGE. The gate's own container is `CONTAINER_BASE`:

    uv run --frozen python docs/reviews/check-merge-invented.py --range 8695101..HEAD
    -> TOTAL merges=95 invented_lines=119
       73dd717  cc=7226B   invented=53
       a881344  cc=13279B  invented=38
       92cb89b  cc=7429B   invented=22
       f2a7bce  cc=2151B   invented=6

**FOUR merges carry invented content, and this ruling originally mentioned one.** Three of them -
`a881344`, `92cb89b`, `f2a7bce`, 66 lines between them - are not discussed anywhere in `#231`,
`#222`, or the first version of this document.

**THE BASELINE IS STILL NOT WRITTEN, AND THE REASON HAS CHANGED.** It was *"we do not know how much
is reflow"*. That is now measured, so that reason is gone. The reason that replaces it is stronger:
**109 lines of genuine content entered this repository inside merge resolutions, invisible to every
branch diff and every reviewer who read a range, and nobody has read one of them as prose.**
`review-231b` classified them mechanically and said explicitly that it did not read them. Writing a
baseline now would record 109 unread lines as accepted debt and manufacture exactly the coverage
this ruling exists to refuse.

**Reading those 109 lines is the work this ruling hands forward.** One of them was a rule in
`PREAMBLE.md` that governs how every agent files a task, found only because `#222` went looking.
The question for the other three merges is whether any of their 66 lines is that kind of thing.

## What this ruling deliberately does NOT do

- **It does not wire the checker.** That follows the baseline. `check-checkers-are-wired.py`'s
  `UNWIRED_BY_DECISION` entry is UPDATED in this commit, because it said the question *"is open on
  task #222"* and this ruling closes it - what is open is the baseline, not the ruling.
- **It does not choose the ratchet's implementation.** `review-231b` states plainly that it checked
  the mechanism exists and works but did not design or prototype it, so Decision 3's mechanism
  choice is unreviewed and is recorded here as such.
- **It does not re-open `#111`, `#203` or the record convention.**

## What a reviewer must do from now on

Declare `PATHS:` unless the tree was genuinely read. If the range contains a merge, run

    git show --cc --format= <merge> | wc -c

and say what you found. **`--format=` is load-bearing**: without it the commit header and message
are always in the byte count, so the command can never return 0 - `git show --cc b9b59dd | wc -c`
is 236 on a merge this ruling certifies clean. With `--format=` a clean merge really does return 0,
measured on `b9b59dd` and `cd8c938`.

**A non-zero is not automatically a defect** - about one line in nine is reflow, which reads
identically to invention here - but it is a thing you have to have looked at before your
declaration clears it.
