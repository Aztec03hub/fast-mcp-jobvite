# HANDOFF — 2026-09-02 03:35Z, written against compaction

Verified by running it at `8986e64`. `origin/main` is `e845839`; six
commits are ahead of it, LOCAL and DELIBERATELY UNPUSHED — see "Why
nothing is pushed" below, because that is the one thing here you must
not undo without reading.

## READ THIS FIRST: this document has been wrong FIVE times

Version 1 said **"Main is GREEN locally, on every gate"** and listed six
gates, all 0. Every number was true and the claim was false: the gate
that had refused the tree for 127 commits was not on the list.

Version 2 said **"15 trunk commits are covered by no round"**. 15 was a
DISPLAY CAP (`untouched[:15]`); the population printed one line above.

Version 3 said main was `09477ee` and listed five gates that no longer
exist under those names, because #143 consolidated three CI jobs.

Version 4 listed four hand-run probes under "Gates ... run with CI's
exact invocation" when CI ran none of them. True about my terminal,
false about the repository.

Version 5 is THIS one, and its predecessor's error was the same family
again, so it is named rather than quietly fixed: version 4 said
*"THE RUNNING JOB IS THE FIRST TO REACH THE LONG POLE"* about run
`203e5af`. **That run never reached the long pole.** It died at the
secret-scan step, exactly as version 4 itself predicted two sentences
later, and the run that actually reached it is a different one, listed
below. A prediction and a measurement were written in one breath and
only one of them was true.

All five are one defect: **a claim about a whole, evidenced by a sample,
a snapshot, or a prediction.** So every count below carries its
container and its sha, anything CI does not run says so on its line, and
anything not yet observed is marked NOT YET OBSERVED.

## Where the trunk actually is

    origin/main   e845839   pushed to BOTH remotes
    local HEAD    8986e64   SIX commits ahead, all held on purpose

    9c08427  #131  the shared gate records who is mutating
    6de1b4a  #154  a duration tool that will not print a max without n
    d0bdf2a  BASH-1: "all 20" against a population of 39
    1cddd76  the #170 brief
    9ce969f  the restorer never read the `repo=` field it is given
    8986e64  both briefs were missing their §0 tools block

## WHY NOTHING IS PUSHED, and do not undo this casually

    CI run 33582613697   head 22c9873   IN PROGRESS since 02:20:43Z
    CI run for e845839                  PENDING behind it since 03:16Z

**Run 33582613697 is the first in this project's history to reach the
deep harness steps.** Four earlier runs on this trunk were cancelled by
GitHub, which evicts older QUEUED runs in a concurrency group REGARDLESS
of `cancel-in-progress` — the setting protects a RUNNING run, not a
queued one. So every push while that run is queued-or-running costs the
trunk another completed record, and this run is the measurement #154 has
been unable to make for two days.

Push when it concludes. Then record the six commits in the backlog,
which cannot be done before the push: see "The backlog order" below.

## What that run has measured, and it corrects a task headline

Read live from the Actions API at 03:31Z, 51 completed steps of
`Lint, types, tests`, 3193s (53.2 min) between them:

    1270s   U9 HTTP hardening amputation, every row applied
     927s   U0 test controls, all fired
     621s   U1 boot amputation harness ran every row
     331s   U4 client mutation controls, all killed
     118s   U1 boot mutation controls, all fired
      93s   Critical-path coverage amputation
      83s   Default suite, zero skips

    Static gates, supply chain and links    47s   success   (#143's fold)
    CodeQL                                  70s   success

**#154's headline was WRONG and this run is what says so.** The task
said "the U4 client amputation harness is the step holding CI past 73
minutes". U9 and U0 are 69% of the completed time between them, and at
the moment I wrote that sentence U4's amputation had not run at all.
A failing trunk under-reports its own durations, so the ranking I built
was a ranking of the steps that got to run.

`docs/reviews/measure-ci-step-durations.py` (`6de1b4a`) exists so the
next person cannot repeat that: it refuses to print a maximum without
the number of runs that REACHED the step, and separately lists steps
that have never completed at all, because a ranked table can only rank
what finished.

**NOT YET OBSERVED:** the job total, the conclusion, and whether the
trunk has its first green run. Do not write that it does until the run
says so.

## Gates at `8986e64`, and which of them CI actually runs

    ruff check . / ruff format --check .                    0
    mypy                                    0   136 source files
    pytest                    887 passed, 0 skipped, 6 deselected
    pre-commit run --all-files                              0
    check-review-coverage                   1   see the backlog note
    probe-coverage-ratchet                  0   10/10 arms
    check-checkers-are-wired                0   + --self-test 35/35
    check-row-floor-exactness               0   25 harnesses
    check-no-sigpipe-pipelines              0
    check-obligations                       0   31 mappings, 25 verified
    check-clause-citations                  0
    check-landing-published                 0
    measure-xref-population                 0
    check-harness-result.sh                 0   38 container, 31 tallies
    control-stranded-mutation.sh            0   32 arms (was 26)
    probe-131-gate-state.sh                 0   9 assertions, NEW
    check-mirror-liveness-controls.sh       0   14 arms, NEW
    probe-wired-checker-amputation.py       0   14 arms, floor 14, NEW
    scripts/check-harness-anchors.py        0   464 anchors
    shellcheck --severity=warning -x        0

**`check-review-coverage` exits 1 ON PURPOSE right now**: `e845839` is
the backlog top-up commit itself and cannot be in the file it writes.
That tail is inherent and the gate ratchets a SET rather than demanding
a zero for exactly this reason.

**actionlint is NOT INSTALLED on this machine.** CI runs it with
`SHELLCHECK_OPTS=--severity=warning`; I could not, and say so rather
than claiming the gate. That is the whole of what I could not run.

**RUN CI'S EXACT INVOCATION, FLAGS AND ALL.** Broken three times in one
evening: `check-committed-file-types.py` bare (staged set, 0 files, exit
0 — which hid a red trunk for 127 commits), `python3` where CI uses
`uv run --frozen python`, and `actionlint` without its `SHELLCHECK_OPTS`.
Copy the line out of `ci.yml`.

## The backlog order, learned tonight and worth keeping

**Push first, THEN record.** `check-review-coverage.py` measures
`origin/main`, so a line added to the backlog before its commit is on
the trunk reads as recorded-with-nothing-under-it — which is precisely
the drift the SUBJECT column exists to catch. I tried it the other way
and the checker refused, correctly.

Backlog is at 65 recorded = 65 measured plus the one inherent tail.

## Agents live right now

    review-r18    reviews tonight's five gate commits; own worktree,
                  read-only outside its report and the backlog file
    suborch-170   sweeps for retyped counts beside growing containers;
                  owns its sweep tool and its findings .md

Both briefs are `docs/briefs/BRIEF-*.md` and both were dispatched
MISSING their §0 tools block — the Task tools are DEFERRED and absent
from an agent's opening toolset, so every "TaskGet before acting"
instruction in them was unfollowable. Fixed at `8986e64`, and BOTH
AGENTS WERE TOLD BY SendMessage, because an agent that has already read
a brief does not re-read it.

**Panes are the binding cap on dispatch.** Finished agents do not
release their pane, and `Agent` fails outright with "no space for new
pane". Thirteen were held when this shift began; two were stopped
deliberately to make room for these. Check `ListAgents` and stop a
finished one before assuming you cannot dispatch.

## What tonight closed

    #163  the secret gate warns about untracked would-be findings
    #164  the mirror's fourth state - not running at all - has a check
    #149  M-4: the wiring probe runs, in its own job, held to a floor
    #131  the shared gate writes the run state file  (LOCAL)
    #154  a duration tool that carries its reach count  (LOCAL)

Two rulings worth not re-litigating:

- **The `HARNESS-RESULT` container stays `scripts/*.sh`.** Its three
  enforced properties are bash constructs with no Python meaning, and
  what they buy — an aborted harness cannot look like a pass — Python
  already has. `probe-wired-checker-amputation.py` prints the canonical
  line anyway so a future widening can count it.
- **`git add -N` and a `pragma: allowlist secret` convention are both
  REFUSED** as ways to see untracked secret-scan findings. The first
  mutates the index against a standing ruling; the second trades a
  surprise for a habit of silencing the scanner.

## What keeps being true

**A CONTROL THAT CANNOT REACH ITS SUBJECT PASSES ANYWAY, and the
isolated form is not exempt.** `check-mirror-liveness-controls.sh` has
14 arms that all inject JSON so none touches the network — deliberate,
and it means none of them could see that the first LIVE call used the
workflow's PATH where the API takes its FILE NAME. Fourteen green rows
and a 404. Isolation removes the outside world from what a control can
check, so the live call needs its own step and the isolated rows must
say what they cannot reach.

**THE GATES FOUND SIX FAULTS IN MY OWN WORK TONIGHT**, which is the
argument for running all of them before believing any: a `printf | grep
-q` that reports a present string as absent under pipefail; a published
tally field with no printed tally beside it; a control table row with
its columns swapped; a harness with no anchor-failure vocabulary, which
`ci-harness-gate.sh` refused outright; an untracked file that
`check-checkers-are-wired.py` could not see until it was staged; and a
`git status` with no `-C` that measured whatever directory it was
invoked from.

**A STALE NUMBER CAN BE THE SYMPTOM OF A FALSE CLAIM.** BASH-1 said
"all 20 `scripts/*.sh`" against 39 tracked, 37 with the option — and
replacing 20 with 37 would have HIDDEN that "all" was wrong
independently: two members are outside the rule and both are correct.
#170 is the sweep for the rest of that shape.

## What I would pick up first

1. **Watch run 33582613697 to a conclusion, then push the six.** A
   monitor is armed on it. Nothing else should touch the remote first.
2. **Collect `review-r18` and `suborch-170`.** Neither has reported yet.
3. **Finish #154 with the run's job total**, and size the per-harness
   cap from U9's 1270s rather than the inherited 1040s figure — which
   the measurement has already shown to be BELOW the largest real row.
4. **#158 and #9 are PHIL'S**, not mine: `main` has no branch protection
   and zero rulesets, and six OIDC roles use wildcard subject claims.
5. **#160 and #106 stay blocked** on a CodeQL findings before/after and
   on `STANDARDS_TOKEN` respectively.
