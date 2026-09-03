# WORKLOG-116: a timeout bound must appear once

2026-09-01, 07:15 PM CDT. Branch `fix/116-timeouts`, cut from `9e04411`.

## The defect

Every bounded harness held one decision twice:

    timeout 900 uv run --frozen pytest ...
    baseline_rc=$?
    if [ "$baseline_rc" -eq 124 ]; then
      echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."

Change the bound and the message lies, at exit 0, in the exact output a
reader turns to when something has already gone wrong. Watched live while
closing #108: a probe rewrote the timeout to 1 and the message still said
"900s".

## The discriminator, which the brief asked for first

The brief warned that *a pattern matching N sites is a SEARCH, not a
diagnosis* - the previous sweep found only 6 of 14 matched sites were
actually defective. So the question here was: **what separates a site that
needs the fix from one that does not?**

**The answer is that all 70 need it, and the reason is structural rather
than statistical.** Every `timeout` invocation in this repo exists to bound
a step that reports its own expiry, and the reporting branch names the
bound. The shape is always:

    timeout <N> <cmd>       # the operative bound
    rc=$?
    if [ "$rc" -eq 124 ]; then
      echo "... <N>s ..."   # the same bound, retyped

Measured over the container, both sides agree exactly:

| value | `timeout` invocations | echoed `Ns` figures |
|------:|----------------------:|--------------------:|
| 900   | 46                    | 46                  |
| 300   | 14                    | 14                  |
| 120   | 10                    | 10                  |

70 invocations, 70 figures, and pairing each figure to the timeout call
governing its branch gives **0 mismatches**. There is no site where a
figure is a free-standing constant, and no `timeout` call whose value is
not retyped somewhere below it. That is why the answer is "all of them"
rather than a subset.

**What is deliberately NOT converted.** Comments. `# 24m19s and PASSES,
against 27-77s for the steps either side of it` is a dated record of a past
run, not a claim about today's bound. Binding it to a variable would make a
historical measurement move when a future bound changes, which is the
opposite of the property being established. The checker scans `echo` lines
only, and its self-test asserts that a `24m19s` in a comment does NOT fire.

## Counts: the brief's hypotheses vs measurement

| arm | brief said | measured | note |
|---|---:|---:|---|
| baseline | 24 files | **29** | all 900 |
| row | 12 files | **31** | **NOT one value: 900 in 17, 300 in 14** |
| selector | 10 files | **10** | correct |

**The brief's "900 baseline / 300 row / 120 selector" is wrong about the
row arm.** The row arm carries two values, and 17 of the 31 row sites run
at 900, not 300. This strengthens rather than weakens the three-names
ruling: `ROW_TIMEOUT` is genuinely a per-script decision, and a repo-wide
`ROW_TIMEOUT=300` would have silently tripled the bound on 17 harnesses.

**My own first measurement was also wrong**, and in a way worth recording:
`grep -E 'timeout [0-9]'` missed every `timeout -k 30 900` call, which made
four scripts look like they carried a prose "900s" with no timeout at all.
The regex now allows flags between `timeout` and its duration. A pattern
that cannot see one spelling reports its blindness as a finding about the
subject.

## The third shape, which the brief did not mention

`scripts/check-u1-pid1-shutdown.sh` has the same defect by a **different
mechanism**, which is exactly why a `timeout`-shaped sweep does not reach
it:

    sleep 0.2
    waited=$((waited + 1))
    if [ "$waited" -gt 100 ]; then
      echo "  $transport: FAILED - the lifespan never opened within 20s"

The bound is a poll interval times a try count, and the **product** was
retyped as "20s". Three copies of one decision, none derived. Now:

    LIFESPAN_WAIT_SECONDS=20
    LIFESPAN_POLL_SECONDS=0.2
    LIFESPAN_POLL_TRIES=$(awk -v w=... -v p=... 'BEGIN { printf "%d", w / p }')

The bound is the named decision because the bound is what a reader cares
about; the try count is derived from it. Behaviour is unchanged at the
default (20 / 0.2 = 100, the original literal), and under a planted
`LIFESPAN_WAIT_SECONDS=5` the tries become 25 and the message reads "5s".

## Verification: the message MOVES, proved both ways

The load-bearing check is not the diff. It is #108's: plant a changed
value, run, and read what the message actually says.

**Fixed code, `BASELINE_TIMEOUT` planted 900 -> 1**, on
`check-body-cap-controls.sh`:

    harness exit: 4
    ABORT: THE BASELINE HUNG - 1s with no result, on the INTACT tree.

**NEGATIVE CONTROL - pre-fix code at `9e04411`, `timeout 900` planted to
`timeout 1`**, same harness:

    harness exit: 4
    ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree.

Same exit code, same one-second abort, and the pre-fix message is a lie.
That pair is the evidence: the fix, and only the fix, is what moves it.

**All three arms proved separately**, because they are three names and a
baseline-only proof licenses only the baseline:

| arm | planted | message emitted | harness exit |
|---|---|---|---|
| BASELINE | 900 -> 1 | `THE BASELINE HUNG - 1s with no result` | 4 |
| SELECTOR | 120 -> 1 | `SELECTOR PROBE TIMED OUT after 1s` | 1 |
| ROW | 300 -> 1 | `TIMED OUT after 1s - this row NEVER FINISHED` | 0 |

Every plant was proved to have landed with `git diff --stat` before the
run, and proved restored with `git diff --quiet` after.

**On that ROW exit 0**: a harness whose every row timed out still exits 0.
That is not a defect - `ci-harness-gate.sh:246` greps the output for
`TIMED OUT` and fails the step. The division of labour is deliberate and
holds; noted here so the next reader does not re-raise it.

## The container assertion

`scripts/check-timeout-literals.py` asserts the property over
`git ls-files 'scripts/*.sh'` - never a hand-kept list, because a list of
the files to fix is the same defect one level up.

    scanned 38 scripts, 1014 echo lines
    0 retyped seconds figures. Every bound appears once. (#116)
    exit 0

**The zero is proved non-vacuous twice.**

`--self-test` (exit 0) runs the detector over a planted lying line:

    self-test: the retyped literal `300s` FIRES              [ok]
    self-test: the derived `${ROW_TIMEOUT}s` does NOT fire   [ok]
    self-test: the `24m19s` in a COMMENT does NOT fire       [ok]

And an **amputation on the real artifact**, which is the stronger arm:
restoring `check-u5-jobs-controls.sh` to its pre-fix form takes the gate
from exit 0 to **exit 1**, naming all three of its arms:

    scripts/check-u5-jobs-controls.sh:69:  bare `900s` in: ABORT: THE BASELINE HUNG ...
    scripts/check-u5-jobs-controls.sh:110: bare `120s` in: SELECTOR PROBE TIMED OUT ...
    scripts/check-u5-jobs-controls.sh:154: bare `300s` in: TIMED OUT after 300s ...

The checker also exits **2**, not 0, if `git ls-files` returns an empty
container - an instrument failure must not render as a clean tree.

## Replay

Every edit to the 31 timeout-bearing scripts was applied by
`scripts/one-shot/apply-116-timeout-names.py`. Proved, not asserted:
resetting all 31 `scripts/*.sh` to `9e04411` and re-running the one-shot
leaves `git diff HEAD` **empty** over them.

That replay caught a real mistake of mine. My first fix for an `E501` on
the one-shot **rewrapped a string the script WRITES INTO the 31 scripts** -
which would have left a recorded one-shot that no longer reproduces the
tree it produced. The replay is the entire reason a scripted edit beats a
hand-typed one. The line is now split at the source level only and the
emitted bytes are unchanged.

**The pid1 fix is NOT in the one-shot** - it is a single site of a
different shape, applied by hand and recoverable from git alone. Stated so
the replay claim is not read wider than it is: it covers 31 of the 32
changed scripts.

## Gates, each exit code on its own line

    bash -n, all 38 scripts/*.sh                              exit 0
    shellcheck --severity=warning (koalaman v0.10.0, all 38)   exit 0
    ruff check .                                               exit 0
    ruff format --check .                                      exit 0
    mypy                                                       exit 0
    check-timeout-literals.py --self-test                      exit 0
    check-timeout-literals.py                                  exit 0
    check-harness-anchors.py --self-check --floor 458          exit 0  (458 resolved, 34 harnesses)
    check-obligations.py                                       exit 0  (31 mappings, 25 verified, 6 recorded absent)
    check-obligations.py --controls                            exit 0
    check-adr-numbers.py                                       exit 0
    check-clause-citations.py                                  exit 0
    check-coupling-controls.py                                 exit 0
    check-coupling-sweep.py                                    exit 0
    check-cross-references.py                                  exit 0
    check-design-citation-shape.py                             exit 0
    check-design-citations.py                                  exit 0
    check-design-freeze.py                                     exit 0
    check-env-vars-are-declared.py                             exit 0
    check-no-errexit.py                                        exit 0
    check-no-sigpipe-pipelines.py                              exit 0
    check-plan-measurements.py                                 exit 0
    check-resweep-verdicts.py                                  exit 0
    check-row-floor-exactness.py                               exit 0
    check-row-floors.py                                        exit 0
    check-settings-are-read.py                                 exit 0
    check-standards-citations.py                               exit 0
    check-checkers-are-wired.py                                exit 0
    ci-harness-gate.sh check-body-cap-controls.sh              exit 0  (12/12 controls fired)
    uv run --frozen pytest --cov --cov-report=json              exit 0  (887 passed, 6 deselected, 0 SKIPPED, 62.83s)
    check-suite-floor.sh 887                                   exit 0  ("suite floor OK: 887 passed, floor 887")
    check-coverage-floors.py (after the --cov run)              exit 0  (total coverage 97.01%)

887 passed against a floor of 887, with **0 skipped** - a skip is a green
that tested nothing, so the count is reported rather than the word "green".
The floor is exactly met, not exceeded: this branch adds no tests, and
nothing here should move it.

Line numbers in 31 scripts moved by +8. The anchor and citation gates above
are the ones that could have broken on that, and all resolve.

## The ci.yml step, RUN before being handed over

`ci.yml` is Tier 0's file, so this is handed over rather than wired. It has
been executed from this worktree, and these are its real exit codes:

```yaml
      - name: No abort message retypes a seconds figure
        run: |
          set -euo pipefail
          uv run --frozen python scripts/check-timeout-literals.py --self-test || exit 1
          uv run --frozen python scripts/check-timeout-literals.py || exit 1
```

Both lines gated with `|| exit 1` rather than chained, because under
`bash -e` only the LAST command of an AND-list triggers errexit.

## FINDING, outside this task's scope - for Tier 0 to make a task or not

**`check-checkers-are-wired.py` selects its population by PATH, so a
checker in `scripts/` can be unwired forever and the gate still exits 0.**

Its own output says the width plainly:

    Checkers in docs/reviews/: 27

`scripts/check-harness-anchors.py` is a wired checker that is NOT in that
27 - it is wired, but nothing verifies that it stays wired. And
`scripts/check-timeout-literals.py`, added by this branch and deliberately
NOT wired, does not appear either: the wiring gate exits 0 on a tree that
has just gained an unwired checker.

This is the path-allowlist shape the repo has now found several times: a
population picked by directory is blind to the member that lives elsewhere.
It is a sibling of #149 (controls that only ever run by hand) and #152 (a
census that starts from the print statement), and the same remedy applies -
select by KIND, not by PATH, as #115 did for citations.

**Suggested fix**, since every finding ships one: widen the checker's
population to `git ls-files 'scripts/check-*.py' 'docs/reviews/check-*.py'`
and re-run. That will immediately report at least
`scripts/check-timeout-literals.py` as unwired, which is TRUE and is the
gate doing its job - so the widening should land in the same commit as
either the ci.yml step below or a recorded exemption for it. I did not make
this change: widening a gate's population is a ruling, and the protocol puts
rulings at Tier 0.

## What I did NOT settle

- **Whether the 900/300/120 bounds are the right values.** Out of scope:
  this task makes each appear once, it does not re-derive them. #108
  measured ~15x headroom on the 900 baseline; the 300 and 120 arms have no
  such measurement recorded anywhere I could find.
- **Nothing else.** The suite was still running when the rest of this file
  was drafted; it has since finished and its numbers are in the gate table
  above, read from the terminal rather than predicted.

  One note worth keeping: `check-coverage-floors.py` exits **2**, not 0 or
  1, on a tree with no `coverage.json`. That is correct-by-design - it says
  so in its own refusal, *"a search at a path that does not exist returns a
  clean empty, indistinguishable from a real pass"* - and it is why the
  coverage floor is only meaningful after the `--cov` run. Run bare it is
  an instrument failure, not a green.

## What I did not attempt, stated separately

- Wiring the new gate into `ci.yml` (Tier 0's file, by protocol).
- Any change to `docs/DESIGN.md` or the ADRs; nothing here touches the
  frozen design.
- Tier-2 workers: zero spawned. Every step was one or two tool calls, which
  now makes it six runs out of six.
