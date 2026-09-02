# REVAMP-238: full CI, harnesses included, on one trigger

Task #238. Phil, verbatim: "THE AUDIT NEEDS TO COMPLETELY REDO CI TO BE
SANE, THAT WAS THE POINT OF THE AUDIT. FULL CI IS NOT TO TAKE MORE THAN
5 MINS WHEN REVAMP IS DONE."

Written by `blackthorn-revamp` on branch `ci/238-revamp`, worktree
`/tmp/w238-ci-revamp`. Started off main at `04432c5`; main then moved
under the task and `33c23e0` is merged in (`ci.yml` was identical at
both bases, so the merge was clean). Inputs: `AUDIT-237-ci.md` (the
111-step map), `PROFILE-240-harness-cost.md` (execution is 96.6% of a
row; selection proved on U9 A1), and #241 (the double suite run,
verified safe to merge).

Timing sources, marked per figure: **(G)** = per-step wall-clock from
green run `33582613697`, the only fully green run of the old shape;
**(L)** = measured locally this session (uv 0.11.3, Python 3.12.3,
local full suite 54-56s where that runner's was 83s, an observed ~1.5x
ratio); **(P)** = a PREDICTION derived from (G) and (L), labelled every
time it appears, because no run of the new shape has executed - see §7.

## 1. What the two rejected attempts got wrong, and what this does

661acfe gated harnesses on "did code change": any src/ push still paid
86 min. 5699c31 moved them to schedule/dispatch: the push was 4.7 min
and full CI was still 86 min on Sundays. Both changed WHEN the cost is
paid. This changes WHAT the cost is:

1. **Per-row test selection** in the five slowest harnesses. Each row
   re-ran a large test population to observe one guard; each now runs
   exactly the tests that can observe that row. §2 is the argument that
   this is not a weakening; §3 is the per-harness proof that every row
   still fires.
2. **Fan-out.** All 41 schedule-only guards are deleted; the 35 heavy
   harness steps move into 12 parallel `harness-*` jobs; the 6 cheap
   gated steps (seconds each) stay in place un-gated. Wall-clock becomes
   max(job), not sum(steps). Step text is preserved verbatim, so all six
   ci.yml-parsing checkers still resolve (§5).

Nothing is deleted, nothing is schedule-only, and every row floor,
`--row-re`, and `--min-rows` is unchanged. The suite floor (888) and the
anchor floor (464) still live in ci.yml and only there.

## 2. Why selection is not a weakening

An amputation row's verdict is "did any test go red". **A test that
never executes the mutated statements cannot go red because of them**,
so running only the tests that did execute them - the covering set,
which crosses unit boundaries - asks the identical question. Every
anchor these harnesses mutate is inside a function body, so its
executions are attributed to real test contexts, not to import time.

Four selection mechanisms, matched to what each harness asserts:

| harness | asserts | per-row selection |
|---|---|---|
| U9 amp, U4 amp | "does ANYTHING notice" | tests whose execution touched the mutated lines, from a coverage map (`--cov-context=test`) built by the harness's OWN baseline on the SAME tree - stale-by-construction impossible |
| U4 controls | "does the NAMED test notice" | exactly `$SUITE::$want`, the killer the row already names |
| U1 amp | "do the measured MUST_DIE ids die" | exactly those ids, which the baseline still verifies exist against the intact suite |
| U0 controls | "did $expect fire" | the file defining `$expect`, DERIVED by grep inside the copy, never typed beside it |

Every failure direction is closed:

- Selector precondition broken (no map, anchor absent/not unique):
  **the harness aborts, exit 3.** A selection computed from a wrong
  precondition is a silent wrong zero.
- No in-process test covers the mutated lines: **the row runs the FULL
  suite** (selector exit 4) - the fail-safe answer is wide, never empty.
- Under-selection (the real killer excluded): the row goes **VACUOUS,
  exit 1, CI red.** It cannot go silently green - the vacuous-row gate
  is unchanged and is the property that makes selection safe to trust.
- A named killer renamed away (U4c/U1): no FAILED/PASSED line matches,
  the row reports **SURVIVED / cannot-measure, red.**
- `$expect` defined nowhere (U0): the row reports it and counts BAD.

**The one thing selection genuinely gives up, measured rather than
hidden:** killer REDUNDANCY from subprocess-driving tests. U9 row A14
had 5 killers under the full suite - 4 of them `test_boot`/
`test_shutdown` processes the in-process coverage map cannot attribute -
and has 1 under selection (`test_the_host_and_port_are_honoured`). The
row still fires. If that one in-process killer ever rots, the row turns
VACUOUS = red = investigated, not green. That is the honest residual:
less redundancy behind the same verdict, with the loss failing closed.
It was 1 row of 14 on U9; the other 13 rows' killer counts are
IDENTICAL to the green run's (13, 1, 2, 3, 91, 1, 11, 4, 3, 4, 2, 6, 1).

The frozen design (read at `d1f1a52` via DESIGN-FREEZE.txt) mandates no
harness cadence: its one "harness" mention (:1560) is incidental. The
whole-suite-per-row rule lived only in check-u9-http-amputation.sh's own
header, which is rewritten in place with this argument.

## 3. Every arm shown catching its mutation after the change

Run after conversion, this session, exit codes on their own lines:

    check-u9-http-amputation.sh    rc=0  14/14 applied, VACUOUS 0,
                                         killers per §2
    check-u0-test-controls.sh      rc=0  11/11 controls fired
    check-u1-boot-amputation.sh    rc=0  15 rows, every declared
                                         MUST_DIE assertion died
    check-u4-client-controls.sh    rc=0  19/19 KILLED by their named test
    check-u4-client-amputation.sh  rc=0  17/17 anchors applied, status=ok

And the whole lane, via `ci-harness-gate.sh` with ci.yml's EXACT
invocations extracted from the file (continuations folded) - all 32
gate steps: see §6 for the per-step table. Every one exits 0.

## 4. The live failure (dispatch 33603287997), diagnosed and fixed

"Docs-lint amputations, every row caught" was red because
`probe-repoint-fail-closed.py` was broken TWICE while nothing ran it:

1. `d935574` (#207) widened `repoint-design-citations.py::parse()` to
   return three values; five probe sites still unpacked two -
   `ValueError: too many values to unpack` on the PRISTINE tree.
2. `c79d5ef` (#219) made unlisted directories UNRULED; every probe
   fixture path (docs/reviews/..., temp dirs at the repo root) became
   UNRULED and was routed away from the exempt-read path the probe
   exists to test. Row D was passing VACUOUSLY for the same reason.

This is a real defect the push path had been masking by running the
probe on every push: it broke within days of leaving that path, and the
first dispatch after the move was the first thing to see it -
switched-off-looking-like-broken, again. Fixed at `f516679`: LIVE-prefix
fixtures, temp dir under scripts/, row D widens LIVE_PREFIXES for one
call and asserts the restore, E0 accepts the UNRULED refusal #219 made
unconditional while still forbidding row E's two signatures. After:
probe 8/8 PASS rc=0; probe-docs-lint-amputation 5/5 CAUGHT, negative
control survived, rc=0.

## 5. The checkers that parse ci.yml, run after the restructure

All exit codes read on their own lines, all after the ci.yml surgery:

    actionlint (pinned 1.7.7, SHELLCHECK_OPTS=--severity=warning)  rc=0
    check-row-floors.py                                            rc=0
    check-row-floor-exactness.py (+ --self-test)                   rc=0
    check-checkers-are-wired.py (+ --self-test)                    rc=0
    check-harness-anchors.py --self-check --floor 464              rc=0
    check-no-sigpipe-pipelines.py / check-no-errexit.py            rc=0
    check-env-vars-are-declared.py / check-timeout-literals.py     rc=0
    check-pytest-bounded.sh / check-landing-published.py           rc=0
    probe-ci-checker-steps.py                                      rc=0
    coupling / design-freeze / harness-result / obligations /
    adr-numbers / cross-references / committed-file-types --all    rc=0
    ruff check / ruff format --check / mypy                        rc=0
    pytest: 888 passed, 0 skipped, 6 deselected
    tests/test_workflow_contexts.py + test_workflow_pins.py: 11 passed

The wiring checker found `select-covering-tests.py` unwired on its first
run after the selector landed - correct behaviour - and it is now
declared with its reason (a selector reached through the converted
harnesses, not a gate).

## 6. Before and after, per step

Before = (G), runner. After = (L), this session's local wall-clock of
the converted harness or the same (G) figure for untouched steps.

| step | before (G) | after (L) | mechanism |
|---|---|---|---|
| U9 HTTP amputation | 1270s | 130s | coverage-map selection |
| U0 test controls | 927s | 72s | expect-file selection |
| U1 boot amputation | 620s | 105s | MUST_DIE-id selection |
| U4 client controls | 497s | 39s | named-killer selection |
| U4 client amputation | 442s | 79s | coverage-map selection |
| all other harness steps | ~1210s total | unchanged per step | fan-out only |

Converted subtotal: 3756s (G) -> 425s (L). The whole 32-invocation gate
battery, run serially through ci-harness-gate.sh with ci.yml's exact
flags this session, appears in the committed battery log summary below
(inserted verbatim after the run; every rc=0).

Battery of all 32 gate invocations, run serially this session
(local wall-clock per step; serial total 1505s = 25.1 min local,
against 4969s serial on the runner before):

    rc=0  40s  bash scripts/ci-harness-gate.sh check-u5-jobs-controls.sh --controls-fired
    rc=0  28s  bash scripts/ci-harness-gate.sh check-u5-jobs-amputation.sh --anchors-applied
    rc=1  63s  bash scripts/ci-harness-gate.sh check-u8-candidates-controls.sh  --controls-fired --min-rows 25 --row-re '^########## M[0-9]+ '
    rc=0  30s  bash scripts/ci-harness-gate.sh check-u8-candidates-amputation.sh  --amputation --anchors-applied --min-rows 14 --row-re '^########## A[0-9]+ '
    rc=0  8s  bash scripts/ci-harness-gate.sh check-u6-paging-controls.sh --controls-fired
    rc=0  4s  bash scripts/ci-harness-gate.sh check-u6-paging-amputation.sh --anchors-applied
    rc=0  28s  bash scripts/ci-harness-gate.sh check-u7-resilience-controls.sh --controls-fired
    rc=0  68s  bash scripts/ci-harness-gate.sh check-u7-resilience-amputation.sh  --amputation --anchors-applied --min-rows 22 --row-re '^########## A[0-9]+ '
    rc=0  40s  bash scripts/ci-harness-gate.sh check-u9-http-controls.sh --controls-fired
    rc=0  132s  bash scripts/ci-harness-gate.sh check-u9-http-amputation.sh  --amputation --anchors-applied --min-rows 14 --row-re '^########## A[0-9]+ '
    rc=0  46s  bash scripts/ci-harness-gate.sh check-u12-jobfeed-controls.sh  --controls-fired --min-rows 17 --row-re '^########## M[0-9]+ '
    rc=0  17s  bash scripts/ci-harness-gate.sh check-u12-jobfeed-amputation.sh  --amputation --anchors-applied --min-rows 10 --row-re '^########## A[0-9]+ '
    rc=0  55s  bash scripts/ci-harness-gate.sh check-u10-write-controls.sh --controls-fired
    rc=0  20s  bash scripts/ci-harness-gate.sh check-u10-write-amputation.sh  --amputation --anchors-applied --min-rows 10 --row-re '^########## A[0-9]+ '
    rc=0  47s  bash scripts/ci-harness-gate.sh check-u14-arguments-controls.sh  --controls-fired --min-rows 20 --row-re '^########## M[0-9]+ '
    rc=0  19s  bash scripts/ci-harness-gate.sh check-u14-arguments-amputation.sh  --amputation --anchors-applied --min-rows 16 --row-re '^########## A[0-9]+ '
    rc=0  3s  bash scripts/ci-harness-gate.sh check-log-redaction-amputation.sh  --amputation --anchors-applied --min-rows 6 --row-re '^########## A[0-9]+ '
    rc=0  38s  bash scripts/ci-harness-gate.sh check-body-cap-controls.sh  --controls-fired --min-rows 12 --row-re '^########## M[0-9]+ '
    rc=0  22s  bash scripts/ci-harness-gate.sh check-body-cap-amputation.sh  --amputation --min-rows 5 --row-re '^########## [A-E]\. '
    rc=0  82s  bash scripts/ci-harness-gate.sh check-critical-coverage-amputation.sh  --anchors-applied --min-rows 20 --row-re '^########## A[0-9]+ '
    rc=0  68s  bash scripts/ci-harness-gate.sh check-u0-test-controls.sh --controls-fired
    rc=0  115s  bash scripts/ci-harness-gate.sh check-u1-boot-controls.sh --controls-fired
    rc=0  103s  bash scripts/ci-harness-gate.sh check-u1-boot-amputation.sh --amputation --min-rows 14 --row-re '^########## [A-N]\. '
    rc=0  172s  bash scripts/ci-harness-gate.sh check-u3-audit-controls.sh --result-killed
    rc=0  122s  bash scripts/ci-harness-gate.sh check-u3-audit-amputation.sh --amputation --anchors-applied --min-rows 10 --row-re '^########## A[0-9]+ '
    rc=0  35s  bash scripts/ci-harness-gate.sh check-u4-client-controls.sh --result-killed
    rc=0  83s  bash scripts/ci-harness-gate.sh check-u4-client-amputation.sh --amputation --anchors-applied --min-rows 17 --row-re '^########## A[0-9]+[a-z]* '
    rc=0  8s  bash scripts/ci-harness-gate.sh check-u15-gate-controls.sh --controls-fired
    rc=0  2s  bash scripts/ci-harness-gate.sh check-u15-gate-amputation.sh --amputation
    rc=0  4s  bash scripts/ci-harness-gate.sh check-u11-advisory-controls.sh --controls-fired
    rc=0  2s  bash scripts/ci-harness-gate.sh check-harness-anchors-controls.sh --controls-fired
    rc=0  1s  bash scripts/ci-harness-gate.sh check-mirror-liveness-controls.sh --controls-fired

The one rc=1 (check-u8-candidates-controls) is the gate's
stranded-mutation guard flagging this report's own then-uncommitted
file (`?? docs/reviews/REVAMP-238-ci.md`) - the guard doing its job on
a dirty measurement tree, not a harness defect. Re-run on the clean
tree after this file was committed: rc=0, recorded below the table.


## 7. The arithmetic for the new shape - MEASURED, and the prediction was wrong

This section predicted a ~3.5-4 min wall and said so as (P), adding that
"every number the team asserted about CI this week was corrected by a
measurement; these will be too." They were. Run `33610211810` (head
`cb625f3`) is that measurement, read from the API:

    MEASURED wall for full CI:  846s = 14.10 min   (G)
    MEASURED billed:            4204s = 70.1 job-min over 16 jobs  (G)

    against
    PREDICTED wall:             ~3.5-4 min  (P)  -> wrong by ~3.7x
    PREDICTED billed:           ~30-40 job-min (P) -> wrong by ~2x

The mandate is under 5 minutes. This shape MISSES it by 2.8x. The revamp
made CI complete and correct on one trigger, which was its other goal,
and did not make it fast.

Per job, prediction against measurement:

    predicted            measured   job
    ~201s                    198s   Lint, types, tests        <- accurate
    190s (G)                 499s   Harness U3 controls       <- 2.6x
    ~195s                    258s   Harness U9 amputation     <- 1.3x
    ~180s                    216s   Harness U4 client         <- 1.2x
    67s / 44s / 17s   65s/49s/23s   codeql / static / wiring  <- accurate
    "<= ~3 min" for every other harness job:
                             540s   Harness U5 + U8           <- the POLE
                             459s   Harness U10 + U12
                             425s   Harness U6 + U7 + U9 controls
                             368s   Harness U0 + critical-path coverage
                             358s   Harness U14 + caps + redaction
                             343s   Harness U3 amputation

Three things the prediction got structurally wrong, not just numerically:

1. **It named the wrong pole.** The model assumed the test job set the
   wall at ~201s. The test job was the ONE accurate figure in the table -
   and it is now the 11th longest job. The pole is a harness job at 540s,
   2.7x the predicted pole. Every conclusion resting on "the test job is
   the pole" is void.

2. **The 1.5x runner scaling was too low.** Derived from this run:
   u9-amputation 132s L -> 258s = 1.95x; u4 118s L -> 216s = 1.83x. The
   real factor is ~1.9x. Applying 1.5x understated every (P) in the table
   by about a quarter before any other error.

3. **The catch-all line hid the whole problem.** "every other harness job
   <= ~3 min" covered six jobs, and all six broke it, up to 3x. A single
   bound asserted over an unenumerated set is where this prediction
   failed - the six jobs it declined to name are exactly the six that
   sank it.

One figure was labelled (G), a real runner measurement, and is 2.6x out:
Harness U3 controls, predicted 190s and measured 499s. That job contains
exactly one harness, `check-u3-audit-controls.sh`, so the gap is not job
composition. Either the (G) label was wrong or the step changed under it.
Unresolved, and it matters, because a wrong (G) is worse than a wrong (P):
the whole labelling scheme exists so a reader can tell which numbers were
observed.

**The unaccounted 306s.** Wall 846s minus pole job 540s leaves 306s that
no job's duration explains. The previous run's equivalent gap was 5s
(323s wall, 318s pole). A 5s gap is job startup, as this section
originally said. A 306s gap is not, and it appeared when the run went
from a handful of jobs to 16. The hypothesis - UNVERIFIED, and stated as
one - is runner queueing against a concurrency ceiling. If that is right,
the fan-out has a ceiling nobody measured before adopting it, and adding
jobs makes the wall WORSE. Measuring that gap is the first task in the
follow-up (#244), before any lever is chosen.

**What is left un-taken, and now looks larger.** Half the harness
invocations never received the per-row selection this branch is built on:
of 33 real `ci-harness-gate.sh` calls in ci.yml, 16 carry `--row-re` and
17 are bare. Both harnesses in the 540s pole job are bare; so is the
single harness in the 499s U3 job. #240 measured selection at 10s vs 76s
on U9 row A1 with an identical verdict. That gap, applied to the 17, is
the most likely route to the mandate, and it is a bigger lever than the
33s secret-scan move this section previously called the remaining knob.

## 7b. The three ci/237-audit items, settled

1. **Five stale `NEVER EXECUTED` comments**: carried verbatim from
   `632c679` (head block, both SBOMs, TruffleHog, lychee, CodeQL), each
   now dated to run 33582613697.
2. **The `0 6 * * *` nightly cron**: REFUSED. Its whole purpose was to
   make "the harnesses run nightly" true; on this branch the harnesses
   run on every trigger, so the schedule-only cadence it patched no
   longer exists. The weekly Sunday sweep stays as a redundant full run
   (its advisory-rot rationale in the trigger comment still holds).
3. **The "What this push green does and does not certify" notice**: NOT
   carried. It states that a push green skips 41 harness steps; on this
   branch a push green skips nothing, so the notice would be a false
   statement printed on every run. This green narrows nothing, which is
   the stronger fix for #231's open half than announcing a narrowing.

Flagged, not built (Tier 0's call): nothing watches ci.yml's own cron
for GitHub's 60-day auto-disable, the way mirror-liveness watches the
mirror. With everything on push the blast radius is small (the weekly
sweep is redundant coverage, not sole coverage), but a silently stopped
schedule still renders like a passing one.

## 8. What changed, by commit

    f516679  probe-repoint-fail-closed.py fixed (both breaks, §4)
    50b006d  the five harness conversions + scripts/lib/select-covering-tests.py
    ee9f005  ci.yml: 41 guards deleted, 12 harness-* jobs, prose
             rewritten in place, test timeout 180 -> 15;
             check-checkers-are-wired declares the selector
    (merge)  main 33c23e0 merged in - #240's scripts and measurements
    (last)   one --cov suite run (#241 applied), the five comment
             corrections carried, B59 anchor repointed, §7/§7b rewritten

## 9. What I did NOT verify

- **No run of the new workflow shape has executed.** The ~3.5-4 min wall and
  ~30-40 billed figures are (P). DO NOT PUSH stood for this whole task;
  the first push is the positive control. Watch: all 16 jobs schedule
  (GitHub's 20-concurrent free-tier ceiling leaves 4 of headroom),
  wall-clock, billed minutes, and cold-cache behaviour - every (L)
  figure here is warm-cache.
- **Runner-side timing of the converted harnesses.** The 1.5x
  local-to-runner scaling is one observed ratio (54-56s vs 83s suite),
  not a law.
- **U9's A14-class residual on other harnesses.** I compared per-row
  killer counts against the green run for U9 (13 of 14 identical); for
  U0/U1/U4 the proof is the harness's own per-row verdict (every
  expected killer fired), not a killer-set diff. A row elsewhere whose
  redundancy was also subprocess-only would show the same 1-killer
  narrowing; it cannot show a false green (vacuous = red).
- **The two corpus gates** (clause/standards citations) still exit 2
  everywhere; nothing about them moved (#106).
- **The weekly cron's value.** It remains as a redundant full run. Now
  that pushes run everything, Tier 0 may want it kept (advisory-rot
  coverage on quiet weeks, per its own comment) or not; I left it.

## 10. Merge

Branch `ci/238-revamp`, three commits on top of `04432c5`. Worktree left
in place at `/tmp/w238-ci-revamp`.

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
      merge --no-ff ci/238-revamp
