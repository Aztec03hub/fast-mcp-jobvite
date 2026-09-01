# HANDOFF — 2026-09-01 06:40 PM CDT, written against compaction

Verified by running it at `09477ee`, not recalled. Main is `09477ee`,
pushed to both remotes.

## READ THIS FIRST: this document has been wrong twice, the same way

Version 1 said **"Main is GREEN locally, on every gate"** and listed six
gates, all 0. Every number was true and the claim was false: the gate
that had been refusing the tree for 127 commits was not on the list.

Version 2 said **"15 trunk commits are covered by no round"**. 15 was
`check-review-coverage.py:298`'s DISPLAY CAP (`untouched[:15]`); the
population printed one line above it. **I read the rows the instrument
chose to show and called it the population** — while describing the
first error.

Both are one defect: **a claim about a whole, evidenced by a sample the
instrument chose.** So the table below lists every gate including the
failing one, and every count carries its container.

## Gates at `09477ee`

    check-cross-references                       0   5 docs, was 3
    check-cross-references --controls            0   3/3, was 2/3
    check-design-citations                       0
    check-design-citation-shape                  0
    check-design-freeze                          0
    check-checkers-are-wired                     0   80 steps, ALL workflows
    check-checkers-are-wired --self-test         0   26/26, NOT WIRED (#149)
    probe-ci-checker-steps                       0   13 of 78, ci.yml ONLY
    probe-ci-checker-steps-control               0   4/4 arms
    probe-r14-manifest-marker                    0   7/7 arms
    probe-142-exempt-controls                    0   9/9 arms
    scripts/check-committed-file-types.py --all  0   RUN IT WITH --all
    ruff check . / format --check / mypy         0
    pytest                        887 passed, 0 skipped, 6 deselected
    check-review-coverage                        1   EXPECTED, see #119

**Two counts, two containers, both right**: 80 is every workflow, 78 is
ci.yml alone. They now say so on the line. A count without its container
is not a measurement.

**RUN CI'S EXACT INVOCATION, FLAGS AND ALL.** `check-committed-file-
types.py` run bare selects the STAGED set — zero files on a clean tree,
exit 0, having opened nothing. That hid a red trunk for 127 commits. I
repeated the mistake an hour after recording it, using `python3` where
CI uses `uv run --frozen python`. Copy the line out of `ci.yml`.

## CI, and the rule is now MEASURED under load

`46dafe0`'s run was still `in_progress` after FOUR later pushes. **The
protection held**: `cancel-in-progress: github.ref != 'refs/heads/main'`
does protect a running run on main. The four runs I evicted (`e119e75`,
`3a8b239`, `cd7e211`, `d486c47`) each had **0 jobs, 0 started** —
pending, consuming nothing. The push cadence was right, and this is the
first time that rule has been tested with pushes stacked rather than
reasoned about.

**CI has still never produced a green run on this trunk.** Before
tonight it could not: the whole-tree file-type gate refused every commit
from `e4f568d` on. Two runs concluded as failures (`be13055`,
`76bc497`). There are TWO workflows per SHA — read the one you mean, and
a CONCLUDED run is not a GREEN run.

## Agents live

**`suborch-148`** — worktree `fmj-worktrees/w148`, branch
`fix/148-150`. Closing #148 (four amputations survive all 22 controls)
and #150 (the ci.yml-mutating control's restore path). Its highest-value
item is a SWEEP: `git diff` used where `git diff HEAD` was meant, found
independently in TWO files tonight — a shared-source bug, not a
coincidence.

**`tally-shapes`** — #120, worktrees `tally-shapes` and `tally-rebuild`.
**DO NOT PRUNE OR CLEAN EITHER.** u9's harness legitimately takes 1040s,
above the probe's 900s default (#146). It corrected itself tonight: it
had exempted a harness by reading its SOURCE for phrases that never
reach its OUTPUT — half a paired source, called an answer. Exemption is
now one harness, not two.

## Unmerged branches

    fix/tally-shapes-work        4 ahead   in flight, do not touch
    fix/tally-shapes             1 ahead   the probe's worktree
    fix/kind-not-path            1 ahead   SUPERSEDED, kept as a record
    rescue/adr-0024-scan-bound   1 ahead   pre-existing, unexamined
    rescue/r6-probe-half-open    1 ahead   pre-existing, unexamined

## What tonight established

**DISPATCH THE REVIEWER BEFORE THE MERGE.** Both review dispatches found
HIGH findings in work already green on every gate — one in a fix I had
written an hour earlier and argued for in three places. **The defects
were in what the code CLAIMED about itself, and no gate reads claims.**

**Five Tier-1 runs, ZERO Tier-2 workers.** The fan-out permission has
never been used. The value is the worktree and the obligation to return
a measurement. Stop budgeting for fan-out.

**All five corrected their brief and every correction held.** A report
with no correction is now the ANOMALY.

**Three instrument disagreements, one shape**: `A..B` is not two
ancestor tests; 80 vs 78 was every workflow vs ci.yml; 389 vs 115 was
the wrong `CONTAINER_BASE`. The arithmetic was right every time and the
POPULATIONS differed. When instruments disagree, do not re-count — find
where each one's population starts and stops.

**A probe cannot amputate its own subject.** Its tree-clean guard
refuses to run against the modified checker, so guard and coverage are
in tension. The R14 reviewer needed a scratch repo to find the survivor.

**A referent says whose NUMBERING, not whose SUBJECT** (#139). That
reframing closed 19 of 46 unresolved references and dissolved a doubt
about whether a survey of an external corpus may cite our sections.

## What I would pick up first

1. **Collect `suborch-148`, merge, and finish the `git diff HEAD`
   sweep** across `docs/reviews` and `scripts` — two instances found
   means look for more.
2. **`tally-shapes`'s u9 pass**, which unblocks #116.
3. **#119** — 115 commits covered by no round, and they are mostly the
   REVIEW MACHINERY: `docs/reviews` + `scripts` is 150 of 233 file
   touches, `src/` + `tests/` is 17. That is ONE round declaring
   `PATHS: docs/reviews scripts .github`, not fifteen. Read them: a
   declaration is a claim by its author, and the checker says so on
   every run.
4. **#143** — job consolidation, held all evening because agents were
   live on `ci.yml`. Do it when the tree is quiet.
