# FLOOR-CONTROLS - the other nine floors, watched firing

Task #91. Branch `chore/floor-controls`, based at `27c6944`. Worktree `/tmp/floor-controls-work`.
Not merged, not pushed. `ci.yml` untouched, and no file under `src/` or `tests/` changed. One
harness changed, by exactly one number: section 3.

**All nine floors that had never been watched fire have now been watched fire.** Nothing is left in
the "representative subset" fallback the brief allowed for; the budget turned out to be about ninety
minutes of harness runtime, not most of a day, because a control run deletes rows and so runs a
harness with FEWER rows than a normal run, not more.

## 1. The nine, and the exact line each one printed

Every line below is copied out of the run's own output. The control derives the floor from the
harness's source with `grep`, computes `rows - floor + 1` as the number of rows to remove, and
requires both the floor's own message and the harness's own exit code.

| Harness | Rows | Floor | Removed | The line the floor printed | Exit |
|---|---|---|---|---|---|
| `check-harness-anchors-controls.sh` | 9 | 9 | 1 | `::error::8/9 ROWS - THE HARNESS LOST ROWS.` | 1 |
| `check-suite-floor-amputation.sh` | 4 | 4 | 1 | `::error::3/4 ROWS - THE HARNESS LOST ROWS.` | 1 |
| `check-u0-test-controls.sh` | 11 | 11 | 1 | `::error::10/11 ROWS - THE HARNESS LOST ROWS.` | 1 |
| `check-u1-boot-controls.sh` | 23 | 23 | 1 | `22/23 ROWS - THE HARNESS LOST ROWS.` | 1 |
| `check-u11-advisory-controls.sh` | 15 | 15 | 1 | `ABORT: 14/15 ROWS - THE HARNESS LOST ROWS.` | **6** |
| `check-u15-gate-controls.sh` | 15 | 15 | 1 | `14/15 ROWS - THE HARNESS LOST ROWS.` | 1 |
| `check-u3-audit-controls.sh` | 15 | 15 | 1 | `########## 14/15 ROWS - THE HARNESS LOST ROWS.` | 1 |
| `check-u4-client-controls.sh` | 19 | 19 | 1 | `########## 18/19 ROWS - THE HARNESS LOST ROWS.` | 1 |
| `check-u7-resilience-controls.sh` | 31 | **31** | 1 | `30/31 ROWS - THE HARNESS LOST ROWS.` | 1 |

The tenth floor, `check-u15-gate-amputation.sh`, was already proved by
`docs/reviews/check-row-floor-control.sh` and is not re-measured here.

`check-u7-resilience-controls.sh` appears with the floor section 3 raised it to. Before that fix its
floor was 26 against 31 rows, so its control had to remove SIX rows and the line it printed was
`25/26 ROWS - THE HARNESS LOST ROWS.`, also exit 1. Both runs are real; the table carries the one
that measures the harness as it now stands.

Four distinct tally shapes appear in that column - `::error::`, bare, `##########`, and `ABORT:` -
and one distinct exit code. Both were found by reading before the first run, and both would have
broken a control written to one shape.

## 2. The design I chose, and why it is not the one section 8 proposed

ROW-FLOORS-REPORT.md section 8 proposed letting `ROW_FLOOR` be overridden from the environment, so
that a control is one run per harness at an impossible floor. **I verified that rather than adopting
it, and did not adopt it.** Three reasons, in order of weight:

1. **It proves strictly less.** Raising the threshold fires whatever the counter happens to hold -
   including a counter wired to nothing. That is not a hypothetical: it is precisely the state
   `check-u15-gate-amputation.sh` was in before task #79, and an impossible-floor run against that
   harness would have reported the floor working. Removing rows and requiring the printed count to
   fall by exactly the number removed is the amputation; raising the threshold is only a mutation of
   the threshold.
2. **It saves nothing.** Both designs are one harness run. The override was proposed as the cheap
   alternative to "delete a row, run, restore, run", but the baseline arm is unnecessary: the floor's
   own message names both numbers, so `14/15 ROWS` is unambiguous whatever else the harness did. A
   control run is in fact CHEAPER than a normal one, because the deleted rows do not execute.
3. **It costs surface in production code.** It is a change to ten harnesses that adds a
   lowering-capable environment variable to each, and `ROW_FLOOR="${ROW_FLOOR:-15}"` no longer matches
   `check-row-floors.py`'s `^\s*ROW_FLOOR=(\d+)\s*$`, so all ten would report as floorless. The
   control I wrote touches no harness permanently at all.

The result is `docs/reviews/check-row-floor-controls.sh` (plural), a table-driven sibling of the
existing singular control. It reuses that file's discipline verbatim: refuse a dirty subject file,
take the backup BEFORE arming the restore trap, assert the edit landed with `cmp`, restore by
byte-copy and check against `HEAD` rather than by re-editing.

## 3. FINDING (Medium), FIXED at `cc99f6c` - u7's floor was five rows behind its harness

It held **31** rows against a floor of **26**. Five rows could have been deleted from it with CI
silent, which is why its control had to remove six before the floor would say anything.

This is not a typo. `ROW_FLOOR=26` was derived from a real run, at `b9a6b1d` on `chore/row-floors`,
which branched from `20e71ed`. `M28`-`M32` were added by `1e55129` on `feat/scan-bound`. Neither
commit is an ancestor of the other:

```
$ git merge-base --is-ancestor 1e55129 b9a6b1d ; echo $?
1
```

Both branches were correct in isolation and the merge produced a floor five rows behind its harness.
**A floor derived on a branch is a measurement of that branch**, which is the same shape as the
"branch-local floors" note that appears in tasks #45, #57, #64 and #69 - but those are about a floor
that is too HIGH after a merge, which fails loudly. This is the quiet direction.

**Fixed, not just reported.** `ROW_FLOOR=31` at `cc99f6c`, derived two independent ways that agree:
the control's own run (`25/26 ROWS` with six rows removed puts the live count at 31) and
`grep -cE '^mutate "' scripts/check-u7-resilience-controls.sh` -> 31. The comment above the floor now
records why the old number was honest and still went stale, so the next reader does not have to
re-derive the history.

**Then the new floor was proved tight**, because a raised floor is itself only a typed number until
it is watched. Re-running the control against the new value needs one row removed instead of six:

```
floor (from source): 31
rows to delete     : 1   (rows - floor + 1)
row invocations still matching: 30 (was 31, must be 30)
30/31 ROWS - THE HARNESS LOST ROWS.
exit with 1 row(s) deleted: 1 (must be 1)
```

**What is NOT fixed** is the mechanism. Nothing in this repository compares any floor to a live row
count, so the next merge can do this again to any harness. The remedy I would propose - a
`--rows-exact` mode on `docs/reviews/check-row-floors.py`, which already enumerates every harness and
both floor layers and lacks only a row pattern per harness - is larger than this task and is filed as
**task #102**, together with the eighteen harnesses whose floors have never been compared to a live
count at all.

## 4. FINDING (Medium) - my own control had this exact defect, and it left a file behind

Recorded because it is the most useful thing in this report, and because the first eight runs all
passed while it was present.

The first version removed a row by deleting its first line and every following line held by a
trailing backslash. That is how a person skimming reads a continuation, and it is wrong: a row's
ARGUMENTS may themselves contain newlines. `check-u7-resilience-controls.sh` row `M2` passes a
single-quoted Python fragment spanning four lines. The backslash rule stopped at the first of them
and left three lines of Python sitting in the harness as loose shell.

**Every check that version had, passed.** `cmp` saw a change. `bash -n` parsed the wreckage without
complaint. The row count fell by exactly six, so the printed `25/26 ROWS` was right. The only visible
trace anywhere was an **empty file named `=`** in the repository root, created by the orphaned
fragment, which `git status --porcelain` showed as `?? =` when I ran the gates - fifty minutes after
the run that made it.

The fix does not compute the extent of a row at all. Prefixing the call with the `:` builtin hands
the whole logical command - quotes, embedded newlines and all - to bash's own parser, which consumes
it and does nothing. A row in a here-document is data rather than a command, so `check-u15-gate-
controls.sh` deletes its line instead; that is the table's fifth column. Two checks were added at the
same time: the count of lines still matching the row pattern must have fallen by exactly the number
removed, and a row carrying a command substitution is refused rather than measured, because `:` still
expands its arguments.

**All nine results in section 1 are from the corrected mechanism.** The eight that were not
contaminated were re-run anyway rather than reasoned about, because a number produced by an
instrument I had just found a defect in is not a number I want in a table.

## 5. What the control checks, one row at a time

For each harness it derives, never types:

- the floor, by `grep -oE '^[[:space:]]*ROW_FLOOR=[0-9]+[[:space:]]*$'` on the harness itself;
- the row count, as matches of that harness's row pattern plus a declared count of rows the pattern
  cannot see. That third column exists because `check-harness-anchors-controls.sh` has **nine** rows
  and only **eight** `row "..."` call sites - its `F1` row is written inline, incrementing `TOTAL`
  directly. A control that enumerated call sites alone would have predicted 8 and reported a mismatch
  against a perfectly healthy harness. I found that by running the harness intact and reading
  `9/9 controls fired.`, not by reading the source, where I had already counted 8.

and then requires all of: the deletion landed (`cmp`), the remaining row-pattern count fell by
exactly the number removed, the harness still parses (`bash -n`), the floor printed
`<count>/<floor> ROWS`, the exit code equals that harness's own floor exit code, and the harness file
is byte-identical to the backup AND to `HEAD` afterwards.

**Every one of the nine puts its floor check BEFORE its survivor check**, which I verified by reading
each one. That matters: it is why the floor's exit is attributable even on a harness that would have
failed for another reason. `check-u0-test-controls.sh` is the case in point - ROW-FLOORS-REPORT.md
section 2 recorded it as red - and its floor still exits 1 first, on its own line.

## 6. Gates

Every one judged by its own exit code, on its own line, run after the last harness run and with a
clean tree.

- `uv run --frozen ruff check .` -> exit 0, `All checks passed!`
- `uv run --frozen ruff format --check .` -> exit 0, `72 files already formatted`
- `uv run --frozen mypy` -> exit 0, `Success: no issues found in 59 source files`
- `uv run --frozen pytest -q` -> exit 0, **`801 passed, 6 deselected in 48.83s`**, **0 skipped**
- `python3 scripts/check-harness-anchors.py --self-check --floor 415` -> exit 0,
  `OK: all 415 anchors resolve to exactly one hit in their target file (floor 415).`
- `python3 docs/reviews/check-row-floors.py` -> exit 0, `Harnesses: 28`,
  `wired but no floor at either layer: 0`

Both floors were read from `.github/workflows/ci.yml` by `grep` at the moment of running, never
retyped: `check-suite-floor.sh 801` and `check-harness-anchors.py --self-check --floor 415`. The
suite count is EXACTLY the floor and did not move, which is what the brief required - this branch
edits neither tests nor harnesses. `docs/OBLIGATIONS.md` was not touched, so no anchor moved and no
repoint was needed. `shellcheck` is not installed on this machine and CI acquires it through
`actionlint`'s docker step, so the new script is unlinted by it - see section 7.

## 7. What I did NOT verify

- **`shellcheck` over `docs/reviews/check-row-floor-controls.sh`.** `shellcheck: command not found`
  here, and CI reaches it only through `actionlint`, which lints `run:` blocks in `ci.yml` rather
  than files in `docs/`. So the existing singular control is unlinted too, and neither is a
  regression. I could not settle it; running `actionlint` locally would not cover this file either.
  **Suggested fix:** if this file is worth linting, it belongs in the same sweep as
  `docs/reviews/check-row-floor-control.sh`, not in this task.
- **Whether any of the other eighteen floored harnesses is slack the way `check-u7` is.** I measured
  live row counts for nine harnesses only. The other floors - the nine external `--min-rows` in
  `ci.yml` and the internally-floored harnesses from later units - were not in this task's scope and
  none of them has been compared against a live count. This is a specific, cheap thing to settle and
  it is what task #102 is for; I am listing it because it is unsettled, not because it is hard.
- **Whether a floor firing actually fails the CI JOB for `check-u11-advisory-controls.sh`.** I read
  `scripts/ci-harness-gate.sh:206`, `if [ "$rc" -ne 0 ]; then ... exit 1`, which catches exit 6, and
  I did not run the gate wrapper itself around a floored harness. The read is unambiguous but it is a
  read, not a run.
- **Why `setsid` without `-w` returned instantly on the first two runs.** `setsid` forks when the
  caller is already a process-group leader, so those two controls ran detached and my "elapsed=0s"
  was a measurement of the fork, not of the harness. Both completed correctly and both were re-run
  under `setsid -w` for section 1, but I did not go back and establish that this is what happened
  rather than something else about the harness.

## 8. Housekeeping

- Three commits on `chore/floor-controls`; not merged, not pushed.
- One file added, `docs/reviews/check-row-floor-controls.sh`, plus this report, plus the one-line
  floor change and its comment in `scripts/check-u7-resilience-controls.sh`. Nothing under `src/`,
  `tests/` or `.github/` is touched on this branch.
- `git status --porcelain` was checked immediately after every interruption. One run was killed by a
  ten-minute tool ceiling mid-harness; the control's `EXIT` trap had already restored the file and the
  tree was clean, which is the behaviour the trap exists for.
- The stray empty `=` file described in section 4 was untracked and has been removed. It is the only
  thing either mechanism left behind.
- No two harnesses were ever run concurrently. Two other agents were running `pytest` in their own
  checkouts during this work (`/tmp/r7-fixes-work` and the shared checkout); neither is this worktree,
  and I confirmed the paths before assuming so.
- **Worktree `/tmp/floor-controls-work` removed** after confirming the branch ref and both commits are
  reachable from the main checkout with it gone. The branch ref is the only copy - nothing is pushed.
