# HANDOFF — 2026-09-02 04:48Z, written against compaction

Verified by running it at `33fc977`, which is this file's PARENT.
**`origin/main` is `6e4fae3` and 23 commits were held there** —
`git rev-list --count origin/main..HEAD` returned 23 at `33fc977`, so it
reads 24 once this commit lands, and rises with every commit after.
**Do not trust the digit; run the command.** Every number below was
derived at that sha by the command beside it, not carried forward.

## READ THIS FIRST: this document has been wrong SIX times

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

**VERSION 6 WENT FALSE BY STANDING STILL.** Its numbers were right when
written and it opened with *"`origin/main` is `d0f8d85` and nothing is
held locally"*. Twenty-three commits later that was the most misleading
sentence in the file, and nothing about version 6 was wrong — it simply
described a tree that had moved. **A handoff's freshness is part of its
correctness**, so this version leads with the held count, which is the
number that goes stale first.

## Where the trunk is

    origin/main   6e4fae3   NOT what is checked out
    local HEAD    33fc977   23 commits ahead, PUSH DELIBERATELY HELD
    DESIGN freeze d1f1a52   (docs/DESIGN-FREEZE.txt; blob verified equal)
    ADRs          35        ls docs/adr/[0-9]*.md | wc -l
    scripts/*.sh  39        git ls-files -- 'scripts/*.sh' | wc -l
    backlog       80 recorded, holding

## What is HELD, and why the push is held

Twenty-three commits: R18's eight fixes, R19's seven findings closed,
ADR-0034 + ADR-0035 with two re-freezes, `suborch-170`'s eleven-commit
merge, and the R19 report.

**The hold is a rule, not a hesitation.** The trunk has exactly one
green run in its history (`33582613697`, head `22c9873`). A second green
run is what would establish that the first repeats, and pushing over a
queued run cancels it — GitHub supersedes older QUEUED runs in a
concurrency group regardless of `cancel-in-progress`. So: push, then
WATCH THAT RUN TO A CONCLUSION before pushing again.

**Only Phil pushes and merges.** Brief him on exactly what the push
changes before it lands so he can watch it.

## THE TRUNK IS GREEN, and this is the first time that sentence has been true

    CI run 33582613697   head 22c9873   SUCCESS

    Static gates, supply chain and links     45s   (#143's three-job fold)
    CodeQL                                   70s
    Lint, types, tests                    86.6min

Every earlier run in this project's history either failed or was
cancelled. **`startup_failure` is 0 across every workflow ever**, so the
0-job cancellations are genuine supersessions, not parse errors.

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

The per-harness default is 1800s. **The largest real row is 1270s,
n=1** — 1.42x headroom over the largest OBSERVED row. No cap was
changed: one observation is a lower bound on a maximum.

## Gates at `33fc977`, and which of them CI runs

    ruff check . / ruff format --check .                    0
    mypy                                    0   137 source files
    check-review-coverage                   0   backlog 80, holding
    check-checkers-are-wired                0   131 members, 72 wired,
                                                59 unwired-with-reason
                                                + --self-test 35/35
    check-design-freeze                     0   blob equal
    check-clause-citations                  0
    check-obligations                       0   31 mappings
    check-row-floor-exactness               0
    probe-mirror-zero-refs.sh               0   3/3, floor 3   NEW
    shellcheck --severity=warning -x        0

**actionlint is NOT INSTALLED here.** CI runs it with
`SHELLCHECK_OPTS=--severity=warning`; I could not, and say so rather
than claim the gate. That is the whole of what could not be run.

**RUN CI'S EXACT INVOCATION, FLAGS AND ALL.** Broken three times in one
evening: `check-committed-file-types.py` bare (staged set, 0 files, exit
0 — which hid a red trunk for 127 commits), `python3` where CI uses
`uv run --frozen python`, and `actionlint` without its `SHELLCHECK_OPTS`.

## Agents and panes

`suborch-187` is live on the floor-container widening, worktree
`fmj-worktrees/w187`, branch `fix/187-floor-container`. Everything else
is stopped.

**`TaskStop` DOES free a pane — my previous version said it does not,
and that was wrong.** Stopping eight agents took window 3 from 13 agent
panes to 5. What is actually binding is GEOMETRY: at 272x50 a window
holds about six panes, so `Agent` fails with "no space for new pane"
well before any count limit. Stop finished agents before concluding you
cannot dispatch, and check `tmux list-panes -a` rather than `ListAgents`
alone — some panes belong to OTHER sessions and must not be touched.

**Every brief must carry §0 VERBATIM.** The Task tools are DEFERRED and
absent from an agent's opening toolset, so "TaskGet before acting on any
assignment" is unfollowable without it, and its failure is silent: the
agent finds no such tool and improvises.

## What tonight established, beyond the individual fixes

**A FIX THAT REPLACES A COUNT MUST NOT WRITE ANOTHER COUNT.** ADR-0034
ruled that a stale ADR count is DELETED, not corrected. Its own
blockquote then said 33; R19 caught it; I "fixed" it to 34; ADR-0035
landed one commit later and made it 35. The corrected number was false
before it was committed, inside the record that forbids the mistake.

**A RATIO IS A JOIN, AND A JOIN OVER TWO POPULATIONS IS WRONG EVEN WHEN
BOTH NUMBERS ARE RIGHT.** "21 of 94 steps disable errexit" — 94 counts
NAMED steps, 17 of which are `uses:` steps that execute no shell and can
never be members. The numerator could only come from the `run:` steps,
which were 86 at that moment and are 87 now because the very commit that
corrected the sentence added one. Found because the tool printed a
smaller step count across MORE files one line below its own docstring.

**A CONTROL THAT REPORTS INSTEAD OF ASSERTING IS NOT A CONTROL.** The
mirror push step's comment said "mirroring nothing and mirroring
everything must not both read as success" and shipped an `echo` of the
ref list. Nothing counted it. In a step that has never once executed,
because there has never been a MIRROR_TOKEN.

**A REPORT THAT WAS WRITTEN IS NOT A REPORT THAT WAS COMMITTED.**
`REVIEW-R18.md` exists in NO git object — written into a worktree that
was then removed. `REVIEW-R19.md` was reachable from exactly one ref
until this session merged it. Task #4 records the same loss for R1.
That is #192.

**MY OWN INSTRUMENTS MISLED ME THREE TIMES IN ONE HOUR**, each nearly
published as a finding about someone else's work: `| head` gave Python
exit 120 and I read it as a gate failing; a positive control passed when
it should have failed because the file it tested was UNTRACKED and the
container is `git ls-files`; and two path guesses returned clean empties
from directories that do not exist.

## What I would pick up first

1. **Collect `suborch-187`** and fold `fix/187-floor-container`.
2. **Push, then WATCH THE RUN TO A CONCLUSION.** One green run is not a
   repeatable green run.
3. **#192 first among the new ones**: make committing the report part of
   the reviewer brief, not an assumption.
4. **#158 and #9 are PHIL'S**: `main` has no branch protection and zero
   rulesets, and six OIDC roles use wildcard subject claims.
5. **#106 and #160 stay blocked** on `STANDARDS_TOKEN` and on a CodeQL
   findings before/after.
6. **#162 is a standing hazard, not a task to close.** A `TaskUpdate`
   re-emits the original description as a fresh assignment. Catch it
   TEXTUALLY; `assignedBy` has read `team-lead` for an agent's own echo,
   so the social tell fails.
7. **`review/r18` must NOT be merged** — superseded, and merging it
   would revert `probe-131-gate-state.sh` from 341 lines to 190.
