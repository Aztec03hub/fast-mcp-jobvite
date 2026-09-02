# WORKLOG — #151: the coverage gate becomes a ratchet

2026-09-01 07:34 PM CDT. Written by Tier 0, on `main`, while
`suborch-143`, `146`, `147` and `152` were live elsewhere in the tree.

## The ruling being implemented

`check-review-coverage.py` returned 1 whenever any trunk commit was
uncovered. **On a trunk anyone is still committing to, that gate is red
by construction**: every merge adds commits no round has yet examined.
A gate that can never be green gets switched off, and this repository
has already watched 119 consecutive CI failures go unread for exactly
that reason.

So the question changes. Not *"is everything reviewed?"* — which has no
attainable yes — but *"did the unread set change without anyone saying
so?"*, which is answerable and is the thing worth gating.

## What shipped

`docs/reviews/review-coverage-backlog.txt` records every outstanding
commit as `<short sha> <KIND> <subject>`. The checker measures the same
set and **fails on any difference**.

**A SET, NOT A COUNT.** A count lets one commit entering and another
clearing cancel to zero. The `CANCEL` arm of the probe is exactly that
case, and it is the arm a count-based ratchet fails.

**BOTH KINDS, and I got this wrong first.** My first implementation
ratcheted `NONE` only. `PARTIAL` is 39 right now, so that gate would
still have been red by construction — I had rebuilt the defect I was
removing, one column over. `NONE` (no round's range contains it) and
`PARTIAL` (a round claimed the range but not every file it touches) are
different facts; the backlog records which, and a commit moving
`NONE -> PARTIAL` is progress the ratchet reports rather than swallows.

**THERE IS NO `--write-backlog`, DELIBERATELY.** A gate that regenerates
the baseline it then checks certifies whatever it just saw — measured
three times in an hour here with `detect-secrets`. The checker prints
the exact lines to paste; adding them is a human act, in a diff, in a
commit whose message has to say why the backlog grew.

**AN ABSENT BACKLOG IS EXIT 3, NOT AN EMPTY ONE.** A missing baseline
that reads as "nothing outstanding" is a false green. So is a malformed
kind silently skipped, and so is a duplicated sha. All three refuse as
broken instruments.

## The numbers, each with its container

    Review documents in the population                      16
    Excluded, with a reason                                 40
    Trunk commits on origin/main since 8695101             258
    Fully covered - range AND every path                   200
    PARTIALLY covered                                       39
    COVERED BY NOTHING                                      19
    Backlog recorded, and measured                          58   = 39 + 19
    probe-coverage-ratchet.py                              8/8 arms

`#119` said the backlog was 115. It is 19 `NONE` today because **R15
landed in between** (`8132017`, "NONE 131 -> 0, PARTIAL 0 -> 39") and 19
commits have accrued since. The 115 was true when written and is not
true now; the ratchet is what stops that number drifting unread again.

## The control, and the trap it had to avoid

`docs/reviews/probe-coverage-ratchet.py`, 8 arms: BASELINE, ENTERED,
CLEARED, CANCEL, KIND, MISSING, MALFORM, DUPLICAT. All pass.

**No arm modifies the tree.** The obvious way to write this probe is to
edit the real backlog and put it back — and a harness killed mid-row
then leaves the edit behind for the next run to blame on someone else.
That is #131 and #146, and I reproduced it by hand an hour ago: I ran
the audit-shape control twice in one bash call, hit my own two-minute
timeout, and stranded its two plant files in the tree. The plant file's
own docstring predicted it: *"If this file is present in a commit, the
control script died without cleaning up and the tree is dirty."*

So the checker grew `--backlog PATH` and every arm points at a temporary
file. The fix for a class of defect is to make the dangerous shape
unnecessary, not to be careful.

## NOT DONE, and why

**The gate is NOT WIRED into `ci.yml`.** `suborch-143` owns that file
this run (per-job minute rounding) and two agents writing one workflow
is how a merge resolution puts damage back. Wiring is a one-step change
and belongs in the same commit as #153's widening, which is also
waiting on `ci.yml`.

Until it is wired **this gate is green-and-inert**, which must not be
confused with green-and-passing. It exits 0 today because the backlog
matches, and nothing runs it but a person.
