# WORKLOG 148 + 150 - the checker integrity layer

Branch `fix/148-150`, cut from `origin/main` at `cd7e211`. Worktree
`repos/fmj-worktrees/w148` (the dispatched one was a worktree of the
outer session repo, not `fast-mcp-jobvite`; made my own, as the
protocol says to).

Two commits: `b27a01e` (#148), `52023ff` (#150).

---

## What the brief claimed, and what I measured

Every number in the brief was a hypothesis. Here is each one against
the measurement.

| brief said | measured | verdict |
|---|---|---|
| 4 amputations survive all 22 controls | 4 survive, 0 rows killed each | **HOLDS** |
| the `-m pytest` row half-covers `_OPT_NO_SCRIPT` | guard removed -> walk yields `pytest`, `_CHECKER_NAME` rejects it, row passes | **HOLDS** |
| `-m coverage`/`trace`/`cProfile` read SILENT | all four (incl. `pdb`) `fires=False` | **HOLDS** |
| the `--` branch is inoperative | no input changes the output; deletion kills 0 rows | **HOLDS, and it is deleted** |
| L-2 blind to the index | `git diff --quiet` exit 0 on a staged file, `--porcelain` non-empty | **HOLDS** |
| "grep `git diff` and fix each" | **WRONG AS AN INSTRUCTION** - see below | **CORRECTED** |
| R14's suggested fix for M-1 | returns `run`, not the script | **WRONG, measured** |
| R14's suggested `_CHECKER_NAME` row | names a file that does not exist; kills nothing | **WRONG, measured** |

### The correction that matters: the sweep

The brief said two authors reached for the same wrong incantation, so
treat `git diff` as a shared-source bug and fix each site. **The sweep
found 14 live sites and only 6 of them are wrong.**

The discriminator is not the command, it is **what the site's restore
compares against**:

    git checkout -- <file>     restores from the INDEX, not HEAD

Measured, in a scratch repo: modify + `git add`, then mutate, then
`git checkout --`, and the file comes back holding the STAGED content
with `git diff --quiet` exit 0 and `git diff --quiet HEAD` exit 1.

So:

| role | sites | reference | ruling |
|---|---|---|---|
| PRE-FLIGHT "refuse to run on a dirty tree" | 5 | must be HEAD-or-wider | **DEFECT** |
| landing "the mutation landed" | 4 | index, matching `git checkout --` | **CORRECT** |
| restore "it came back" | 4 | index, matching `git checkout --` | **CORRECT** |
| post-run tree check, restore is `cp` from a backup | 1 | index | **CORRECT** |

**A blanket rewrite to `HEAD` would have broken 8 working checks**,
making them report `RESTORE FAILED` on a tree that had been restored
exactly as designed. The rule to carry forward is *the dirtiness check
must ask about the same reference the restore writes from*, not
*`git diff` is always wrong*.

Site by site:

- `docs/reviews/probe-ci-checker-steps-control.py:91-97` - pre-flight
  AND landing AND restore, one predicate. **FIXED** to `git status
  --porcelain`. Safe for all three roles *because* the pre-flight is
  asked first and returns False; once ci.yml matches HEAD, index and
  worktree agree and the three readings coincide.
- `docs/reviews/probe-r14-manifest-marker.py:141` - **ALREADY FIXED**
  (`git diff --quiet HEAD`), with the reasoning in a comment.
- `scripts/check-u3-audit-amputation.sh:52` - **FIXED**.
- `scripts/check-u4-client-amputation.sh:47` - **FIXED**.
- `scripts/check-u3-audit-controls.sh:52` - defect, **NOT TOUCHED**.
- `scripts/check-u4-client-controls.sh:51` - defect, **NOT TOUCHED**.
- 8 in-loop checks in those four scripts - correct, left alone, with a
  comment in the two I edited saying why they were left.
- `docs/reviews/probe-audit-row-container.sh:166,168` - correct
  (restore is `cp` from a backup). Separately: **it has no pre-flight
  guard at all**, which is a different gap and not mine.

**The two untouched defects are a deliberate hold, not an oversight.**
`git diff --name-only origin/main...fix/tally-shapes` lists both
`-controls.sh` files; task #120 is live on that branch. Editing them
here reproduces exactly the collision #116 already records. They need
the identical five-line change; Tier 0 should apply it after #120
merges.

---

## #148 - the four survivors

Reproduced first, with a fresh module per arm, `PYTHONDONTWRITEBYTECODE=1`,
against the real file. All four killed **0 rows**.

Then closed. The committed arms are now
`docs/reviews/probe-wired-checker-amputation.py`, which asserts a kill
count per arm rather than printing one:

| arm | killed | which rows |
|---|---|---|
| BASELINE | 0 | - |
| A `_OPT_NO_SCRIPT` emptied | 2 | `-m coverage run`, `-m cProfile -o` |
| B `--` branch REINSTATED (inverse) | 0 | - (this is the proof it was dead) |
| C `_CHECKER_NAME = .*` | 1 | `python3 -u <a real non-checker>` |
| D `_OPT_WITH_VALUE = {-X}` | 2 | `-W error`, `--check-hash-based-pycs` |
| E `_MODULE_RUNNERS` emptied | 2 | the two runner rows |
| F `_runner_script` always None | 2 | the two runner rows |
| G `_INTERPRETER` loses the suffix | 1 | `python3.12 <checker>` |

Five new control rows: 22 spellings -> 27, 26 controls -> 31.

### Both of R14's suggested fixes for this were wrong

- **M-1.** R14 wrote that once `j` advances past the module name, "the
  existing `not opt.startswith("-")` break already steps over
  correctly". It does not. `coverage run <script>` puts a bare `run`
  in the way, the walk breaks there, and `_script_of` returns `"run"`.
  The row would not fire and the fix would look applied. Replaced with
  `_runner_script()`, which scans right past options and sub-commands
  for the first `.py` token - the same suffix `_CHECKER_NAME` demands,
  so it narrows nothing.
- **`_CHECKER_NAME`.** R14's row was
  `python3 -u docs/reviews/notacheck-...py`. That file does not exist,
  `third_party_imports` returns `[]` for a path that does not resolve,
  and the row stays silent whatever the regex is. It kills nothing.
  The subject has to be a REAL non-checker script that needs a third
  party, and it is derived, not named.

**The derivation deliberately does not use `_CHECKER_NAME`.** Testing
`startswith("check-")` instead is not duplication for its own sake: a
control that selects its subject *through the construct it tests* is
vacuous, and amputating `_CHECKER_NAME` to `.*` would have made
`_non_checker_subject()` find no subject and raise, rather than
produce a failing row.

### Ruling on the `--` branch: DELETED

`check-checkers-are-wired.py:267-269` could only change the answer for
a token starting with `-`, and `_CHECKER_NAME = ^check-[\w-]+\.py$`
rejects exactly those. Measured: `['python3','--','-x.py'] -> '-x.py'`
with the branch, and `_CHECKER_NAME.match('-x.py')` is `None`, so the
rescue is thrown away one line later. No input exists for which the
branch moves `bare_python_steps`'s output.

The repo has a standing rule against inoperative code, so it is
deleted rather than labelled. The `python3 -- <checker>` row survives
the deletion (arm B) and stays as a **shape** control; a comment at
the generic break records why no special case is needed.

The ruling keeps a live check: arm B puts the branch back and asserts
nothing changes. A deletion undetectable in both directions is the
evidence; a sentence would decay.

### The `-m pytest` row, annotated in place

It is not the `-c`/`-m` control it resembles - with the guard removed
the walk yields `pytest`, which `_CHECKER_NAME` rejects, so it passes
either way. It occupied the space where the real control belonged,
which is worse than an empty space. Left in as a shape control, with a
comment saying so and pointing at the row that does the job.

### A second inoperative half, found and NOT fixed

`_OPT_NO_SCRIPT`'s `-c` member is inoperative for the same reason
`--` was. `python3 -c 'import x' <checker>`: with the guard, `None`;
without it, the walk breaks at the code string and returns that, which
`_CHECKER_NAME` rejects. Both paths stay silent, so **no control can
distinguish `-c` handling**. Unlike `--`, deleting it would be wrong -
`-c` genuinely means "no script", and the guard is right even though
it is unobservable. Reported rather than touched; it is a judgement
for Tier 0.

---

## #150 - the ci.yml-mutating control

- **M-2 fixed**: the `finally` restores only if `BAD` is actually in
  the file. Reproduced before fixing, by pointing `CI` at a temp copy
  and making arm A raise - no kill, real ci.yml untouched.
- **Abnormal exit**: the recovery command is printed BEFORE the first
  mutation. Not tested by killing anything.
- **L-2 fixed**: `git status --porcelain`.

### The probe found a defect in my own fix

`probe-control-restore-guard.py`'s AFTER arm failed on its first run:

    ValueError: '/tmp/tmp7_ci4zaw/ci.yml' is not in the subpath of '<repo>'

My recovery notice used `CI.relative_to(ROOT)`, which raises when the
two are unrelated. The warning about a killed process would itself
have crashed. In production `CI` is always under `ROOT`, so this would
never have fired in normal use - which is precisely why only a probe
that moves `CI` could see it.

### And my own control stranded a mutation

The negative arm ran the real amputation harnesses under `timeout 25`
to prove the guard lets a clean tree through. It does - both reached
`########## BASELINE`. But one run was killed while the harness held a
mutation, and left `M src/fast_mcp_jobvite/audit.py` in the tree. I
caught it in the same turn and restored it (`git status --porcelain --
src/` empty after).

**This is task #131 reproduced accidentally, in my own hands, in a
worktree with committed work in it.** It is the strongest argument I
saw all run for `--restore-only`.

Also worth recording: the first version of that control used
`src/fast_mcp_jobvite/observability/audit.py`, a path I inferred rather
than read. It does not exist, and every check against it returned a
clean empty - the harness "passed" its guard for the wrong reason. The
real path is `src/fast_mcp_jobvite/audit.py`, read out of the script.

---

## Gates, CI's exact invocations, exit codes on their own lines

    uv run --frozen ruff check .                                     0
    uv run --frozen ruff format --check .                            0   124 files
    uv run --frozen mypy                                             0   125 files
    uv run --frozen python docs/reviews/check-checkers-are-wired.py  0   27 checkers, 80 steps
    ... --self-test                                                  0   31/31 controls
    uv run --frozen python .../probe-wired-checker-amputation.py     0   8/8 arms
    uv run --frozen python .../probe-ci-checker-steps-control.py     0   4/4 arms
    uv run --frozen python .../probe-control-restore-guard.py        0   2/2 arms
    uv run --frozen pytest                                           0   887 passed, 0 skipped,
                                                                         6 deselected
    python3 scripts/check-harness-anchors.py --self-check --floor 458  0  458 anchors, 34 harnesses
    shellcheck --severity=warning <the 2 edited scripts>              0
    bash -n <the 2 edited scripts>                                    0

Floors derived from `ci.yml`, not retyped: `check-suite-floor.sh 887`
and `--floor 458`. The suite is EXACTLY at its floor, not slack.

`git status --porcelain -- .github/workflows/ci.yml`: empty before and
after every run. `git status --porcelain -- src/`: empty at submission.

---

## What I could NOT settle

- **Whether the two `-controls.sh` guards should be fixed by the same
  five lines or folded into #120's rewrite.** I can see the collision;
  I cannot see #120's final shape, and reading its worktree while its
  harness runs is what the protocol forbids. Tier 0 has both.
- **Whether `_MODULE_RUNNERS` is the right closed set.** I took R14's
  five and added nothing. `python3 -m memray run`, `-m pyinstrument`,
  `-m line_profiler` have the same shape and are not in it. A closed
  list is blind to the member nobody added; whether the answer is a
  longer list or a different rule (any `-m <x>` followed by a `.py`
  token) is a design call, and the second would change behaviour for
  `-m pytest tests/foo.py`. Not mine to rule.
- **Whether `probe-ci-checker-steps.py` is wired at all.** `grep -n
  "probe-ci-checker-steps" .github/workflows/ci.yml` returns nothing;
  only `check-checkers-are-wired.py` appears, at `:241`, without
  `--self-test`. That is R14's M-3 and task #149, and I did not widen
  into it.

## What I did NOT attempt

- Wiring anything into `ci.yml`. Both new probes are unwired on
  purpose; that is #149.
- The `scripts/check-*-amputation.sh` harness shape with the canonical
  `HARNESS-RESULT` line (#149). A half-formed canonical line would be
  worse than none, so neither probe emits one.
- The 36 multi-line blocks (#147), and `probe-audit-row-container.sh`'s
  missing pre-flight guard.
- Running the full `-amputation.sh` harnesses to completion. They were
  run only far enough to prove the guard's two directions.

## Worktree

`repos/fmj-worktrees/w148` is LEFT IN PLACE with both commits on
`fix/148-150`. I do not merge or push. Remove it after merging.
