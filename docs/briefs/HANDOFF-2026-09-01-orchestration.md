# HANDOFF — 2026-09-02 05:42Z, written against compaction

Verified by running it at `72fe217`, this file's PARENT. `origin/main` is
`6e4fae3`; `git rev-list --count origin/main..HEAD` returned **55**
there, so it reads 56 once this commit lands and rises with every commit
after. **Do not trust the digit; run the command.** Every number below
was derived at that sha by the command beside it.

## READ THIS FIRST: seven versions, and what each one got wrong

Versions 1-5 each asserted a whole from a sample: a "green on every gate"
list missing the gate that had been red for 127 commits; a display cap
read as a population; five gate names that no longer existed; four
hand-run probes listed as CI gates; and a run declared to have reached
the long pole two sentences after its own paragraph predicted it would
die earlier.

**VERSION 6 WENT FALSE BY STANDING STILL.** Every number in it was true
when written, and it opened *"nothing is held locally"*. Twenty-three
commits later that was the most misleading sentence in the file.

**VERSION 7 WENT FALSE ONE COMMIT LATER**, in the way it had just warned
about: it said "backlog 80 recorded, holding" in two places, and the
backlog became 66 at `a0677bc` - the very next commit. **So v8 writes no
digit it can avoid**, and where a number is unavoidable it carries the
command that produces it.

## Where the trunk is

    origin/main   6e4fae3   NOT what is checked out
    local HEAD    72fe217   PUSH DELIBERATELY HELD
    DESIGN freeze d1f1a52   docs/DESIGN-FREEZE.txt; blob verified equal
    ADRs          35        ls docs/adr/[0-9]*.md | wc -l

    held commits  git rev-list --count origin/main..HEAD
    backlog       uv run --frozen python docs/reviews/check-review-coverage.py

## Why the push is held, and what would release it

The trunk has exactly ONE green run in its history (`33582613697`, head
`22c9873`). A second would establish that it repeats. **Pushing over a
queued run cancels it** - GitHub supersedes older QUEUED runs in a
concurrency group regardless of `cancel-in-progress` - so: push, then
WATCH THAT RUN TO A CONCLUSION before pushing again.

**Only Phil pushes and merges.** Brief him on exactly what a push
changes before it lands so he can watch it.

## Gates, and how to run them

    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/check-checkers-are-wired.py
    uv run --frozen python docs/reviews/check-clause-citations.py
    uv run --frozen python docs/reviews/check-obligations.py
    uv run --frozen python docs/reviews/check-design-freeze.py
    uv run --frozen python docs/reviews/check-design-citations.py
    uv run --frozen python docs/reviews/check-row-floor-exactness.py
    uv run --frozen python docs/reviews/check-brief-report-references.py
    bash docs/reviews/check-brief-report-refs-controls.sh
    python3 docs/reviews/check-row-floor-exactness.py --self-test
    uv run --frozen ruff check . ; uv run --frozen ruff format --check .
    uv run --frozen mypy ; shellcheck --severity=warning -x docs/reviews/*.sh scripts/*.sh

All green at `72fe217`.

**actionlint is NOT INSTALLED here.** CI runs it with
`SHELLCHECK_OPTS=--severity=warning`; say so rather than claiming it.

**READ EACH EXIT CODE ON ITS OWN LINE.** Three verification shapes bit
me in one session, all one family:

    cmd >/dev/null && echo "OK"     # && short-circuits; under set -e only
                                    # the LAST command of an AND-list
                                    # triggers errexit. Hid a ruff red.
    rc=0; cmd; rc=$?; echo "$rc"    # REPORTS a failure without stopping.
                                    # I committed over a red gate once.
    Briefs scanned: 0 ... rc=0      # WORST: a SUCCESS the gate had not
                                    # earned, over a directory that did
                                    # not exist. That is #205.

The commit scripts now end with an explicit `REFUSING TO COMMIT ON RED`,
and it has blocked two commits that would otherwise have landed red.

## Agents live right now

    review-r21    reviewing c749334..main in fmj-worktrees/r21
    suborch-204   the bare `:NNN` citation form, in fmj-worktrees/w204

**`TaskStop` DOES free a pane.** What binds is GEOMETRY: at 272x50 a
window holds about six panes, so `Agent` fails with "no space for new
pane" well before any count limit. Check `tmux list-panes -a`, and note
some panes belong to OTHER sessions and must not be touched.

**Every brief must carry §0 VERBATIM.** The Task tools are DEFERRED and
absent from an agent's opening toolset, so "TaskGet before acting" is
unfollowable without it, and its failure is silent.

**RECORD A REVIEWER'S REPORT AS IN FLIGHT IN THE SAME COMMIT AS ITS
BRIEF.** A brief naming its report CITES it, so
`check-brief-report-references.py` goes red until the report lands.
Learned by hitting it three times after the fact.

## Rulings made this session, none of them yet reviewed

- **ADR citations are AS AT acceptance and are NOT repointed**
  (`docs/adr/README.md`). 46 of 64 measured DRIFTED. No gate was red -
  `check-design-citations.py` proves a line EXISTS - so this is a
  convention, not a fix. The SHA-per-ADR remedy was refused because it
  ALREADY EXISTS in five ADRs and already failed: ADR-0019 names its
  blob and all four of its citations drifted anyway.
- **The brief-report gate cannot tell a CITATION from a QUOTATION, and
  that false positive is ACCEPTED** (its docstring). Remedy is to
  rewrite the prose. An EXEMPT marker was refused on the measured
  47->61 inflation a bare-substring marker already caused here.
- **The obligation is REPORTING; filing a task is the brief's to grant**
  (`PREAMBLE.md`). It contradicted `PROTOCOL-sub-orchestrators.md` and
  an agent was caught between them.

## What tonight established, beyond the individual fixes

**A COUNT I WROTE WAS WRONG FOUR TIMES, EVERY TIME FROM A SELECTOR WITH
A LOOSE OR MISSING EDGE.** A regex with no left boundary read
`CODE-REVIEW-CHECKLIST.md` as a shorter name and I published that as a
finding; `grep -c` over a table counted its header row; "twelve ADRs"
was five; a step denominator moved four times in one day. **The only
reason the last was caught is that another agent's number disagreed.**

**A DATED PAST-TENSE FIGURE ONLY RESOLVES AN AMBIGUITY COARSER THAN THE
RATE THE FIGURE MOVES.** Every commit in the range carried the same
date, so the date could not disambiguate 86 from 90.

**A CLEAN MERGE SAYS NOTHING ABOUT WHAT IT OVERWRITES.** An agent
yielded to my version, reverted its own hunk, and verified zero
conflicts - but I had already hand-resolved both into a superset, so its
clean merge would have replaced the superset with the weaker half.

**A REFUSAL THAT MISDIAGNOSES IS WORSE THAN A BARE ONE.** The floor
control told me a `.sh` file "is not bash". Two members, two different
reasons, one hardcoded sentence asserting the wrong one for half of them.

## What I would pick up first

1. **Collect `review-r21` and `suborch-204`.**
2. **Push, then WATCH THE RUN TO A CONCLUSION.**
3. **#194's remaining half**: `probe-131-gate-state.sh` CAN be watched -
   read `rows=N` from a first run rather than predicting it;
   `probe-wired-checker-amputation.py` needs its own `--self-test`.
4. **#158 and #9 are PHIL'S**: no branch protection, zero rulesets, and
   six OIDC roles with wildcard subject claims.
5. **#106 and #160 stay blocked** on `STANDARDS_TOKEN` and a CodeQL
   before/after.
6. **#162 is a standing hazard** and its row no longer carries a count,
   because the population is "sightings someone happened to mention".
7. **`review/r18` must NOT be merged** - superseded. Merging it would
   shrink `probe-131-gate-state.sh` to its 190-line version. Derive both
   rather than trusting a digit here; main's has grown twice since this
   warning was first written, and the pair is:

       git show review/r18:docs/reviews/probe-131-gate-state.sh | wc -l
       wc -l < docs/reviews/probe-131-gate-state.sh
