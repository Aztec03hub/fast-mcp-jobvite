# HANDOFF — 2026-09-01 05:50 PM CDT, written against compaction

Everything below was verified by running it at `be13055`, not recalled.
Main is `be13055`, pushed to both remotes.

## READ THIS FIRST: the previous version of this document was wrong

It said **"Main is GREEN locally, on every gate"** and listed six gates,
all 0. Every one of those six numbers was true. **The claim was still
false**, because `check-committed-file-types` was not on the list — and
that gate had been refusing the tree for 127 commits.

**A universal claim ("every gate") evidenced by an enumeration is only
as good as the enumeration**, and the member that is missing is never
the one you thought of. This is the same defect as R14-H1 and #139,
found three times in one evening in three different artefacts, and the
third instance was this handoff. See the gate table below: it now lists
**every** gate including the ones that fail, because a handoff that
lists only passing gates teaches the next reader the same mistake.

## Gates at `be13055`, all of them, exit codes read one per line

    scripts/check-committed-file-types.py --all      0
    check-design-citations                           0
    check-design-citation-shape                      0
    check-design-freeze                              0
    check-checkers-are-wired                         0
    check-settings-are-read                          0
    check-env-vars-are-declared                      0
    check-no-errexit                                 0
    check-obligations                                0
    check-cross-references                           0
    check-row-floors                                 0
    check-row-floor-exactness                        0
    check-no-sigpipe-pipelines                       0
    ruff check .                                     0
    ruff format --check .                            0
    mypy                                             0
    check-review-coverage                            1   <-- EXPECTED
    pytest                          887 passed, 0 skipped, 6 deselected

**`check-review-coverage` exits 1 by design and is NOT wired.** **115**
trunk commits are covered by no round - **not 15**. I reported 15 here
and in a commit message. 15 is `check-review-coverage.py:298`'s DISPLAY
CAP (`untouched[:15]`); the population prints one line above it. **I
read the rows the instrument chose to show and called it the
population** - the same defect this document opens by describing,
committed while describing it. Found by R14-R1. The caps are not even
consistent: `:298` shows 15, `:300` shows 10, and neither says how many
it hid. That is #119's blocker, and the number only falls when a round
declares those commits.

**RUN THE INVOCATION CI RUNS, ARGUMENTS AND ALL.** `check-committed-file-
types.py` bare selects the STAGED set; on a clean tree that is zero
files and it exits 0 having opened nothing. The `--all` above is not
decoration. The gate now prints `[staged set]` or `[whole tree]` and
shouts when a staged run examined nothing, so this specific trap is
closed — but the habit is the fix, not the message.

## CI

`be13055` is the first push after the trunk-red fix and a run was still
in progress when this was written. **CI has never produced a green run
on this trunk.** Before that fix it could not: the whole-tree file-type
gate refused every commit from `e4f568d` onward.

Per #105: a RUNNING run on main is protected by
`cancel-in-progress: github.ref != 'refs/heads/main'`; a PENDING one has
consumed nothing. Check `gh run view <id> --json jobs --jq '.jobs|length'`
before deciding whether a push costs anything. Note there are TWO
workflows per SHA — read the one you mean.

## Three agents live, and what each owes

**`review-r14`** — opus, read-only on `review/r14-config`, started
17:42. A fresh adversarial reviewer on the R14 branch, dispatched
BEFORE that branch merges. Owes `docs/reviews/REVIEW-R14-R1.md`
committed on that branch, plus a `SendMessage` with re-measured numbers.
Its brief hands it my figures as HYPOTHESES and tells it to attack the
probe's vacuity, the JSON edge cases, and whether the REVIEW-COVERS
declaration is honest.

**`suborch-144`** — Tier-1, opus, worktree `fmj-worktrees/t144-145`,
branch `fix/144-145-detectors`, 3 commits ahead. #144 + #145 as one
piece: two detectors that cannot see the failure each was written for.
Regex widening FORBIDDEN, shlex token walk required. #145's disposition
deliberately not pre-ruled. Owes spellings measured, controls, its #145
decision.

**`tally-shapes`** — #120, worktrees `tally-shapes` and `tally-rebuild`.
**DO NOT PRUNE EITHER.** Owes the per-harness before/after exit-code
ledger, which is what unblocks #116.

## Unmerged branches

    review/r14-config          6 ahead  DONE, green, awaiting review-r14
    fix/144-145-detectors      3 ahead  in flight
    fix/tally-shapes-work      2 ahead  committed, ledger outstanding
    fix/tally-shapes           1 ahead  the probe's worktree
    fix/kind-not-path          1 ahead  SUPERSEDED by kind-not-path-2
                                        (merged); kept as a record
    rescue/adr-0024-scan-bound 1 ahead  pre-existing, unexamined
    rescue/r6-probe-half-open  1 ahead  pre-existing, unexamined

## Ruled today, so nobody re-opens them

- **The exemption register** (`#142`, merged `76bc497`): a citation is
  exempt only if the line carries the marker AND the `(path, address)`
  pair has a row with a non-blank reason. **Neither half alone** — the
  sub-orchestrator measured that 3 marked pairs also appear on UNMARKED
  lines, so my pair-keyed ruling would have widened three files.
- **Records vs load-bearing** (`a1773e8`): `CHANGELOG.md`,
  `docs/worklogs`, `docs/plans` are RECORDS, out of review-coverage
  scope, each with a stated reason. `docs/briefs` is deliberately IN
  scope — a brief instructs an agent, so a wrong one produces wrong work.
- **#139, re-ruled tonight**: the cross-reference gap is **27 live
  specifications, not 130**. Subtract the records and 106 of the 136
  disappear. 18 of the 27 are ADRs, which are live decisions whose §N
  citations nothing resolves today. Derive the population; do not
  hand-add two files.
- **Never green a safety gate by widening it.** The `.log` that turned
  the trunk red was renamed, not allowlisted. That gate is
  allowlist-first because a confidential vendor PDF and an unlicensed
  RAML reached public remotes on this project once already.

## The instrument lessons this evening produced

Recorded because each one cost real time and all three are the same
shape — **a partial instrument whose exclusion rule shares a cause with
the defect**:

1. **`probe-ci-checker-steps.py` ran 12 of 78 steps** and skipped 36
   "multi-line blocks". A step is a multi-line block precisely because
   it carries a flag, and a flag is what makes CI's invocation differ
   from the bare local one. The sample was anti-correlated with the bug.
   → **#147**.
2. **`A..B` is not two `is-ancestor` tests.** It means reachable-from-B-
   not-from-A and includes side branches that never descend from A. I
   published a false finding on this. The `&&` also hid which half
   failed.
3. **A hand-kept list is blind to the member nobody added** — and in
   R14-H1 the checker's own docstring NAMED the omitted member one
   screen above the list that omitted it.

## What I would pick up first

1. **Collect `review-r14`'s findings, fix, merge `review/r14-config`.**
   It is green and complete; only the round stands between it and main.
2. **`tally-shapes`'s ledger**, which unblocks #116.
3. **#119** — now that #140 has taken PARTIAL to 0, the only thing
   between here and a wireable coverage gate is the 15 NONE commits.
4. **#147** — the probe blind spot, because it is what let #140's
   defect hide, and it will hide the next one.
