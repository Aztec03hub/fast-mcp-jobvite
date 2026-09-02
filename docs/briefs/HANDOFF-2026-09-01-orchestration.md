# HANDOFF — 2026-09-02 04:15Z, written against compaction

Verified by running it at `d0f8d85`. `origin/main` is `d0f8d85` and
**nothing is held locally** — `git rev-list --count origin/main..HEAD`
is 0. Every number below was derived at that sha by the command beside
it, not carried forward.

## READ THIS FIRST: this document has been wrong FIVE times, and the sixth version is the first that was not

Version 1 said **"Main is GREEN locally, on every gate"** and listed six
gates, all 0. Every number was true and the claim was false: the gate
that had refused the tree for 127 commits was not on the list.

Version 2 said **"15 trunk commits are covered by no round"**. 15 was a
DISPLAY CAP (`untouched[:15]`); the population printed one line above.

Version 3 said main was `09477ee` and listed five gates that no longer
existed under those names, because #143 consolidated three CI jobs.

Version 4 listed four hand-run probes under "Gates ... run with CI's
exact invocation" when CI ran none of them.

Version 5 said *"THE RUNNING JOB IS THE FIRST TO REACH THE LONG POLE"*
about a run that died at the secret-scan step two sentences before its
own paragraph predicted exactly that.

**VERSION 6 IS THE FIRST WHOSE PREDECESSOR DID NOT GO FALSE.** Version 5
marked its unobserved claims `NOT YET OBSERVED` and named a run id; the
run then concluded and every marked item resolved without contradicting
anything. That is the fix working, not luck: **the defect was never
being wrong, it was asserting a whole from a sample.** So this version
keeps the rule — every count carries its container and its sha, anything
CI does not run says so, and anything unobserved is marked.

## Where the trunk is

    origin/main   d0f8d85   pushed to BOTH remotes, nothing held
    DESIGN freeze e3b5c97   (docs/DESIGN-FREEZE.txt; blob verified equal)
    ADRs          34        ls docs/adr/[0-9]*.md | wc -l
    scripts/*.sh  39        git ls-files -- 'scripts/*.sh' | wc -l
    backlog       79 recorded = 79 measured

## THE TRUNK IS GREEN, and this is the first time that sentence has been true

    CI run 33582613697   head 22c9873   SUCCESS

    Static gates, supply chain and links     45s   (#143's three-job fold)
    CodeQL                                   70s
    Lint, types, tests                    86.6min

Every earlier run in this project's history either failed or was
cancelled. Runs since have been cancelled by GitHub superseding QUEUED
runs in the concurrency group when a push lands on top — **that is
expected, not a failure**, and it is why a run worth having must not be
pushed over.

### The step table, and it corrected a task headline

68 completed steps in the test job, 5191s of step time:

    1270s  U9 HTTP hardening amputation, every row applied
     927s  U0 test controls, all fired
     620s  U1 boot amputation harness ran every row
     497s  U4 client mutation controls, all killed
     442s  U4 client amputation harness ran every row
     190s  U3 audit mutation controls, all killed

**#154 said "the U4 client amputation harness is the step holding CI
past 73 minutes". It is FIFTH.** U9 and U0 are 42% of the job between
them. A failing trunk under-reports its own durations, so the ranking I
had built was a ranking of the steps that got to run.

The per-harness default is 1800s and rests on an inherited 1040s figure.
**The largest real row is 1270s, n=1** — so 1.42x headroom over the
largest OBSERVED row, not the ~1.7x the old figure implied. No cap was
changed: one observation is a lower bound on a maximum, and this project
has already sized a cap from a maximum that was not one.

`docs/reviews/measure-ci-step-durations.py` refuses to print a maximum
without the number of runs that REACHED the step, and lists separately
the steps that have NEVER completed — because a ranked table can only
rank what finished.

## Gates at `d0f8d85`, and which of them CI runs

    ruff check . / ruff format --check .                    0
    mypy                                    0   136 source files
    pytest                    887 passed, 0 skipped, 6 deselected
    pre-commit run --all-files                              0
    check-review-coverage                   0   79 = 79
    probe-coverage-ratchet                  0   10/10 arms
    check-checkers-are-wired                0   + --self-test 35/35
    check-design-freeze                     0   blob equal
    check-row-floor-exactness               0   25 harnesses
    check-obligations / clause-citations    0
    check-no-sigpipe-pipelines              0
    check-harness-result.sh                 0   38 container, 31 tallies
    check-harness-anchors.py                0   464 anchors
    control-stranded-mutation.sh            0   32 arms  (was 26)
    probe-131-gate-state.sh                 0   12 arms, floor 12  NEW
    check-mirror-liveness-controls.sh       0   16 arms, floor 16  NEW
    probe-wired-checker-amputation.py       0   14 arms, floor 14  NEW
    secrets-baseline --controls             0   9 arms   (was 6)
    shellcheck --severity=warning -x        0

**actionlint is NOT INSTALLED here.** CI runs it with
`SHELLCHECK_OPTS=--severity=warning`; I could not, and say so rather
than claim the gate. That is the whole of what could not be run.

**RUN CI'S EXACT INVOCATION, FLAGS AND ALL.** Broken three times in one
evening: `check-committed-file-types.py` bare (staged set, 0 files, exit
0 — which hid a red trunk for 127 commits), `python3` where CI uses
`uv run --frozen python`, and `actionlint` without its `SHELLCHECK_OPTS`.

## The backlog no longer feeds itself

`review-coverage-backlog.txt` entered `RECORD_PATHS` at `1abb362`. Before
that, a top-up touched that file ALONE and so became an uncovered commit
the NEXT top-up had to record — four commits of pure self-reference. I
met that tail four times and wrote *"the tail is inherent"* into one of
those commit messages. **It was a missing dict key**, and this file's own
docstring already stated the principle.

**The push-then-record ORDER still stands**: the checker measures
`origin/main`, so a line added before its commit is on the trunk reads
as recorded-with-nothing-under-it.

## Agents live right now

    suborch-170   #180 (build the wrong-subject register) then #182.
                  Branch fix/170-retyped-counts in fmj-worktrees/w170,
                  7+ commits, UNMERGED, UNPUSHED. Owns its census tool
                  and findings doc.
    review-r19    the 23-commit fix round, e845839..origin/main.
                  fmj-worktrees/r19. Read-only outside its report and
                  the backlog file.

**Panes are the binding cap on dispatch.** Finished agents do not
release their pane and `Agent` fails outright with "no space for new
pane". Check `ListAgents` and stop a finished one before concluding you
cannot dispatch.

**Every brief must carry §0 VERBATIM from the canonical template.** Two
of mine tonight shipped without it, so their "TaskGet before acting on
any assignment" instruction was unfollowable — the Task tools are
DEFERRED and absent from an agent's opening toolset. Its failure is
silent: the agent finds no such tool and improvises.

## What tonight established, beyond the individual fixes

**A FIX REPLACING A COUNT WITH A SELECTOR NEEDS THE SELECTOR DERIVED.**
ADR-0034 deleted "all eleven ADRs" correctly and put `Type: Deviation`
in its place — inside a FROZEN document. One real deviation was spelled
`Standards deviation`, so it fell outside the selector written to
include it, and the ADR added a fifth spelling itself. Caught by an
agent VERIFYING the fix rather than accepting it.

**A GATE CAN PRINT AN ALL-CLEAR PRECISELY WHERE IT FAILED TO LOOK.**
`git ls-files` output split on whitespace turned `my notes.md` into two
nonexistent paths; the scanner found nothing in either and the gate
printed *"none would be a finding"* over a file holding three. Worse
than silence: it ends the enquiry, and it is most confident exactly
where its input was mangled.

**AN ISOLATED CONTROL CANNOT SEE THE OUTSIDE WORLD IT EXCLUDED.**
Fourteen mirror-liveness rows all inject JSON — deliberate, and it means
not one could see that the first LIVE call used a path where the API
takes a file name. The live call needs its own step.

**THE SAME NOUN CAN NEED OPPOSITE REMEDIES.** "867 citations" is
decoration → delete the digit. "nine wrong-subject citations" is the
EVIDENCE that citations go wrong at a rate worth a checker → build a
register so it derives. Deleting the second would take the argument
with it.

## What I would pick up first

1. **Collect `review-r19` and `suborch-170`.** Neither has reported on
   its current piece.
2. **Watch a run to a conclusion before pushing again.** The trunk has
   one green run; a second would establish that it repeats.
3. **#158 and #9 are PHIL'S**, not mine: `main` has no branch protection
   and zero rulesets, and six OIDC roles use wildcard subject claims.
4. **#106 and #160 stay blocked** on `STANDARDS_TOKEN` and on a CodeQL
   findings before/after.
5. **#162 is a standing hazard, not a task to close.** Its textual
   mitigation fired correctly tonight: an agent refused a completion
   echo by comparing the TEXT, and noted that the social tell would have
   failed because `assignedBy` read `team-lead` rather than itself.
