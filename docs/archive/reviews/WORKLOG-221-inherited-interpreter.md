# WORKLOG #221 - the interpreter never mattered, the venv always did

Agent: `suborch-221`. Written 2026-09-02 01:24 AM CDT.
Branch `fix/221-inherited-interpreter`, rebased onto `main` at `c79d5ef`.
It was rebased TWICE: `main` moved from `2099a72` to `4f03004` while I
measured, and to `c79d5ef` while I wrote this up. Every number below was
re-measured on the final base, and the 25-SAME result held at all three.
Worktree `/tmp/w221-inherited-interpreter` (left in place).

## Headline

**The measurement refutes the task's premise, and the fix is one line in a
checker rather than 25 lines in `ci.yml`.**

    SAME              25
    DIFFERENT          0
    DIFFERENT-OUTPUT   0
    FAILS-TO-RUN       0

All 25 bare-`python3` CI sites give the identical exit code AND identical
normalised output under `python3` and under `uv run --frozen python`. No
`ci.yml` line is rewritten by this branch.

The one real observation - `check-plan-measurements.py` giving `[STALE] M3`,
`[STALE] M4`, rc=1 under `python3` and four passes rc=0 under `uv run` - was
never about the invoking interpreter. It was about whether `.venv` EXISTS,
and `uv run` creates it as a side effect.

## The measurement is the artefact

`docs/reviews/measure-221-interpreter.py`, committed. It:

- **derives** the population from `ci.yml` on every run rather than reading a
  retyped list, and cross-checks the derived COUNT and script set against the
  25 the task recorded at `2099a72`;
- runs each site twice, `python3` then `uv run --frozen python`, with
  `PYTHONHASHSEED=0` and `PYTHONDONTWRITEBYTECODE=1`;
- normalises the absolute repo path and any wall-clock duration out of the
  captured output before comparing;
- classifies each site SAME / DIFFERENT / DIFFERENT-OUTPUT / FAILS-TO-RUN,
  where FAILS-TO-RUN is decided by an import/syntax marker rather than by a
  nonzero code, because a checker's own refusal is also nonzero.

Run it:

    uv sync --frozen
    python3 docs/reviews/measure-221-interpreter.py

**Determinism, verified rather than asserted.** Two runs on the unchanged tree
were byte-identical, checked with `diff -q`, both before and after the rebase.
The brief named a probe on this project that differed by 99 lines between runs
from per-process hash randomisation; that is what `PYTHONHASHSEED=0` and the
duration normaliser are for. The tree was also identical before and after the
whole sweep (`git status --porcelain` diffed against itself), so no checker
being measured left anything behind.

**The census header on current `main`:**

    bare python3 sites: 25
    uv sites (control): 12 at [303, 332, 333, 900, 1060, 1080, 1287, 1298, 1785, 1807, 1952, 1968]
    census size agrees with the record (25 sites)
      line drift since 2099a72 (not a finding): [1566, 1735, 1867] -> [1575, 1744, 1876]
      scripts: 23 distinct

**Two corrections to the task description, both minor and both worth having.**

1. It says *"sibling steps at :303 and :332 ALREADY use `uv run --frozen
   python`"*, implying two. There are **twelve**. The repo is much more mixed
   than the task assumed, which strengthens rather than weakens the
   "nothing distinguishes them" observation.
2. Three of the 25 line numbers had already drifted between `2099a72` (where
   my worktree started) and `c79d5ef` (where it now sits) - the same 25 sites,
   three of them further down the file. The script reports drift as a note and
   only fails the census on a change of COUNT or SCRIPT SET, because a line
   number moving is not a finding and a 26th site would be.

## The two hypotheses, and how they were separated

- **H1** the invoking interpreter decides: bare `python3` lacks the project's
  dependencies, so checkers that import them misbehave.
- **H2** something co-varying with the arm decides: `uv run` SYNCS `.venv`, and
  a checker that locates `.venv/bin/python` for itself changes answer on
  whether that directory exists.

One site's exit code cannot tell these apart. Two things separated them.

**First, the code.** `check-plan-measurements.py:43` at `2099a72` read:

    PYTHON = str(VENV_PY if VENV_PY.exists() else sys.executable)

The probes run pytest as a subprocess under `PYTHON`. So the interpreter that
matters is the one this line picks, not the one on the shebang line.

**Second, the decisive control: hold the interpreter constant, vary the venv.**
Both arms below are `/usr/bin/python3`, same commit, same file, in a clean
worktree at `main`:

    no .venv  -> rc=1
                 "Re-running 4 plan measurements with /usr/bin/python3"
                 [STALE] M3, [STALE] M4
                 "2 plan claim(s) no longer reproduce. Fix the PLAN, not this script."

    uv sync --frozen, then the SAME command
              -> rc=0
                 "Re-running 4 plan measurements with <repo>/.venv/bin/python"
                 [PASS] M1 M2 M3 M4
                 "Every plan measurement reproduces."

The interpreter is identical across those two rows. Only `.venv` changed, and
the verdict flipped. **H1 is refuted; H2 holds.**

And the corollary the brief asked me to look for: **every one of the 25 scripts
imports stdlib only.** I grepped all 23 distinct files for `yaml`, `pytest`,
`httpx`, `pydantic`, `requests`, `tomli`, `jinja2`, `rich` and `click` imports
and got zero hits, which is why bare `python3` is safe for them by
construction. The checker that DOES parse YAML - `check-checkers-are-wired.py`
- is already one of the twelve `uv run` sites, at `:303`.

## Reading the one green run (the thing nobody had done)

`gh` IS available to me, so this is settled rather than inferred. Run
`33582613697`, head `22c9873`, conclusion `success`, three jobs all green. The
static-gates job log (`repos/{owner}/{repo}/actions/jobs/100100671540/logs`,
205,514 bytes) says:

- the workflow uses **both** `astral-sh/setup-uv@v5` and
  `actions/setup-python@v5` at `python-version: 3.12`;
- the step env carries `pythonLocation: /opt/hostedtoolcache/Python/3.12.14/x64`
  and **no `VIRTUAL_ENV`**, so on the runner `python3` resolves to the
  hostedtoolcache interpreter and NOT to `.venv`;
- `uv sync` runs early - *"Creating virtual environment at: .venv"* - so
  `.venv` exists before any of the 25 steps;
- and the step at `ci.yml:665` printed, verbatim:

      Re-running 4 plan measurements with /home/runner/work/fast-mcp-jobvite/fast-mcp-jobvite/.venv/bin/python
        [PASS] M1 ... [PASS] M4
      Every plan measurement reproduces. Known-open items are listed as OPEN above.

**So CI's green is NOT an accident of `PATH`.** `python3` on the runner is the
setup-python interpreter, and the checker selected the venv for its probes on
its own. The conditional risk the task flagged is answered: it does not fire on
the runner, and it was never conditional on `PATH` in the first place.

## The fix, scoped to exactly what the measurement shows

**Nothing in `ci.yml`.** 25 SAME means a blanket rewrite would change 25 lines,
close nothing, and retire the observation that found the real cause.

**One thing in `check-plan-measurements.py`:** the silent fallback is deleted
and replaced by a refusal with its own exit code.

    0  every plan measurement reproduces
    1  a plan claim has gone stale
    2  .venv is absent - NOTHING was judged; run `uv sync --frozen`

This is the defect, stated as a property: *a checker reported a fault in its
own environment using the words and the exit code reserved for a fault in its
subject.* A false red is milder than a false green, and it still cost a whole
task: #221 exists because two readers took `[STALE] M3` at face value.

Exit 2 has a sibling precedent in this repo - `check-coverage-floors.py`
already exits 2 with *"coverage.json does not exist. Run:"* rather than
reporting a floor it could not measure. My measurement observed that live:
`ci.yml:1876` is the one row where both arms return rc=2, identically.

**Proved both ways, end to end:**

    OLD code, no .venv -> rc=1, 2 STALE rows, "2 plan claim(s) no longer reproduce"
    NEW code, no .venv -> rc=2, refusal naming `uv sync --frozen`, ZERO probes run
    NEW code, .venv     -> rc=0, "Every plan measurement reproduces"

`--self-test` carries three arms over the refusal: A1 a present venv returns
that interpreter; A2 an absent one exits `EXIT_NO_VENV` rather than returning
anything; A3 `EXIT_NO_VENV` is not equal to either verdict code, because the
moment it collides the conflation is back.

One detail worth recording because I got it wrong first: `raise
SystemExit("message")` prints the message AND exits **1** - the verdict code.
The message goes to stderr separately and the code is raised as an int.

## The residual, one layer up: the step's diagnostic conflates 1 and 2

`ci.yml:674` (the `if [ "$rc" -ne 0 ]` branch under the `:665` invocation)
prints `::error::a measurement the plan rests a decision on no longer holds`
for ANY nonzero code. With exit 2 in the language, that message is now wrong
for one of the two failure modes - the same conflation, one layer up.

**I have NOT edited `ci.yml`**; it is the orchestrator's file. Here is the hunk,
and I ran it rather than guessing. Insert immediately after `echo "$out"`:

    if [ "$rc" -eq 2 ]; then
      echo "::error::the plan probes had no venv, so nothing was measured - run uv sync --frozen"; exit 1
    fi

Measured, by executing the whole step body under `/usr/bin/bash -e` in two
trees:

    proposed body, .venv present -> exit 0
    proposed body, .venv absent  -> exit 1, "::error::the plan probes had no venv..."
    CURRENT body,  .venv absent  -> exit 1, "::error::a measurement the plan rests a decision on no longer holds"

The third row is the defect, reproduced. The change is cosmetic on the runner
today (the venv always exists there) and is worth taking because the failure it
mislabels is the one that already cost a task.

**`actionlint` is NOT installed in this environment. I did not run it and I am
not claiming I did.** That hunk has never been linted, and CI's own run would
be its first test.

## Gates, each judged by exit code on its own line

Run in `/tmp/w221-inherited-interpreter` after the final rebase onto
`c79d5ef`:

| gate | command | exit | result |
|---|---|---|---|
| lint | `uv run --frozen ruff check .` | 0 | All checks passed! |
| format | `uv run --frozen ruff format --check .` | 0 | 142 files already formatted |
| types | `uv run --frozen mypy .` | 0 | Success: no issues found in 142 source files |
| suite | `uv run --frozen pytest` | 0 | **887 passed, 0 skipped**, 6 deselected, 55.56s |
| wiring | `uv run --frozen python docs/reviews/check-checkers-are-wired.py` | 0 | WIRED: 75, UNWIRED with a stated reason: 63 |
| anchors | `python3 scripts/check-harness-anchors.py --self-check --floor 464` | 0 | measured as row `ci.yml:1152` in the sweep |
| new self-test | `python3 docs/reviews/check-plan-measurements.py --self-test` | 0 | 3 arms, all pass |
| new self-test | `python3 docs/reviews/measure-221-interpreter.py --self-test` | 0 | 8 assertions, all pass |

Both floors were DERIVED from `ci.yml`, not typed from the brief:
`check-suite-floor.sh 887` and `--floor 464`. The suite meets 887 exactly, with
zero skips.

`measure-221-interpreter.py` is recorded EXEMPT in
`check-checkers-are-wired.py` with a reason: it runs the other gates as
subprocesses and compares two arms, so it has no verdict of its own to gate on,
and wiring it would run every static gate twice more for nothing.

## Two reds I found, neither of them mine

**RED 1 - already fixed upstream, no action.** At my original base `2099a72`,
`uv run --frozen ruff check .` exited **1** with 3 errors, all `W505`/`E501` in
`docs/reviews/probe-204-orphaned-by-repoint.py`. I did not touch that file. It
is already fixed on current `main` by `be4fd12`, and ruff over the same file
taken from a pristine `main` worktree exits 0.

**RED 2 - LIVE ON `main` RIGHT NOW, and it is a wired CI gate.** My sweep runs
all 25 sites, so it caught this without looking for it. `ci.yml:265` runs
`docs/reviews/check-no-errexit.py`, and on a PRISTINE detached worktree at
`4f03004`, and still at `c79d5ef` - no file of mine present - it exits **1**:

    Tracked shell scripts checked: 60

    1 script(s) enable errexit:
      docs/reviews/probe-stale-branch-regression.sh:50  set -euo pipefail

The offending file was added by `ebaf6c8` ("A merge can silently delete work,
and the branch it caught was a LIVE one"), and its line 50 is `set -euo
pipefail` sitting directly under a comment block about running the probe before
a merge. The gate's own message states the remedy: use `set -uo pipefail`, and
gate an individual command with `|| rc=$?` or an `if` where the status is read.

I am NOT fixing it. It is another agent's file, outside my scope, and the
PREAMBLE says work found outside scope is REPORTED rather than silently fixed
and my brief grants no `TaskCreate` mandate. **But it means `main` is red today
on a step CI runs, so merging this branch onto it does not make CI green.**
My branch is green on every gate I ran; this red is inherited.

## What I did NOT verify

- **That the hunk above is valid workflow YAML in context.** `actionlint` is
  not installed here. I ran the shell body standalone under `bash -e` in both
  states and read its exit code; I did not parse it as part of `ci.yml`, and I
  did not edit `ci.yml`, so nothing about that suggestion has been through a
  workflow linter.
- **CI itself.** Nothing on this branch has run on a GitHub runner. My evidence
  about the runner is a read of the ONE green run's log (`33582613697`), not a
  new run.
- **Whether any of the 25 sites differ on a runner rather than here.** The 25
  SAME result is measured in this Linux worktree with `.venv` present. The
  runner's `python3` is 3.12.14 from hostedtoolcache; mine is
  `/usr/bin/python3` 3.12.3. Both are 3.12 and all 25 scripts are stdlib-only,
  so I expect no difference, but I could not execute them on a runner and I am
  not claiming I did.
- **`uv run --frozen python` semantics beyond what I ran.** I did not test the
  arms with a STALE lockfile or without network; `--frozen` refuses to resync,
  which is why it is the right arm, but I did not exercise its refusal path.
- **`gh run view --log` for this run returns EMPTY** at exit 0 with no stderr
  - a clean zero that explains itself as nothing. I did not chase why; I went
  to `gh api .../jobs/<id>/logs` instead, which returned 205,514 bytes. Anyone
  relying on `--log` on this repo should know it returns nothing silently.
- **The other 11 `uv run` sites' correctness.** I measured them only as a
  control population count; I did not run or read them.

## Merge

Two commits, rebased onto `c79d5ef` so it fast-forwards. **`main` moved twice
under me tonight**, so if it has moved again this will refuse; rebase or take
a normal merge rather than forcing anything:

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
        merge --ff-only fix/221-inherited-interpreter

The worktree `/tmp/w221-inherited-interpreter` is LEFT IN PLACE as instructed.
The scratch worktree `/tmp/w221-novenv`, used only for the venv-absent control
arms, is removed.
