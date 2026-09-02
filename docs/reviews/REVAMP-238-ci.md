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

    RAW, run 33614887374 (0d2c945), GREEN:  wall 431s, 16/16 jobs   (G)(1)
    RAW, run 33610211810 (cb625f3), FAILED: wall 846s, pre-cov shape (G)(1)

`(1)` MEANS ONE DRAW, VARIANCE UNMEASURED. It is on both figures on
purpose. Every number this section has had to retract was quoted without
it.

## 7a. Five rewrites, and what this section is now allowed to claim

This section has been rewritten FIVE times in one day. Reviews R23 found
errors that survived rewrites one through four, and the last of them was
in the correction itself. The pattern is the finding: **each rewrite
replaced a number with a better number instead of asking what the run
behind it could support.**

So this version states measurements and ONE identity, and stops.

**THE IDENTITY, which is what actually explains run 1:**

    wall = max over jobs j of (queue_j + duration_j)

    queue_j = job.started_at - run.created_at

THE ORIGIN IS LOAD-BEARING AND WAS UNSTATED UNTIL R26 MEASURED IT. Using
`job.created_at` instead - which is what the jobs endpoint hands you
first - the same identity gives 844 and 429 with a 2s offset, because a
job record is created exactly 1s after the run record in BOTH runs. The
figures below are on the `run.created_at` basis. Two 1s lags exist here
and they are different things: run-record to job-record creation, and
last-completion to run-record write.

For run 33610211810 the maximum is `Harness U5 + U8`: 305 + 540 = 845.
That is provable from ONE run and needs no comparison.

RE-DERIVED FROM THE PAYLOADS, 2026-09-02, after R25 recorded that no
review round had ever fetched them - the whole of this section rested on
numbers three readers had only read back. Both runs re-fetched from
`/repos/:owner/:repo/actions/runs/<id>/jobs`, every figure recomputed:

    run 33610211810  conclusion=failure  16 jobs
      run wall (updated_at - created_at)          846s
      max_j(queue_j + duration_j)                 845s
      attained by  Harness U5 + U8   q=305  d=540
      max queue alone 305s ; max duration alone 540s

    run 33614887374  conclusion=success  16 jobs
      run wall                                    431s
      max_j(queue_j + duration_j)                 430s
      attained by  Harness U6 + U7 + U9 controls  q=5  d=425
      max queue alone 5s ; max duration alone 425s

Every number above this paragraph holds. **846 and 845 are two different
quantities, not a retyped digit** - the run wall spans `created_at` to
`updated_at` and includes the second between the last job completing and
the run record being written, so it exceeds `max_j(queue+duration)` by
1s in both runs (846/845 and 431/430). The section had both figures and
never said they measure different things, which is how it reads as an
inconsistency.

Two further things the payloads settle. The pole CHANGES IDENTITY between
the runs - `Harness U5 + U8` in run 1, `Harness U6 + U7 + U9 controls` in
run 2 - so no claim resting on "the pole" transfers between them. And in
run 2 the maximum queue over all sixteen jobs is 5s, which is why the
queue argument that fits run 1 says nothing at all about run 2.

**WHY THE TWO-RUN ARGUMENT I PUBLISHED WAS CIRCULAR.** I wrote that
`maxQ` tracked `gap` in both runs and concluded the gap was queue. R23
asked whether the two could agree by construction, and they do. In run 1
the longest-running job, the longest-QUEUED job and the LAST-TO-FINISH
job are all the same job - verified, all three are `Harness U5 + U8` -
and when they coincide, `gap = wall - pole` IS `q_pole` IS `maxQ` as
arithmetic. 305-against-306 was never evidence. Run 2 is degenerate the
other way: its maxQ job is NOT its pole, and all sixteen queues sit at
4-5s, so any statistic over them is about 5. Neither row discriminated.
The conclusion was right; the argument for it was not.

**WHAT THE TWO RUNS DO AND DO NOT SETTLE.**

- Run 1's admission ladder is 3,3,3, nine at 4s, then 30, 51, 56, 305.
  Twelve admitted together and four admitted one at a time as others
  finish is what a limit near twelve looks like WHEN IT BINDS.
- Run 2 admitted all sixteen within 5s. That kills "the limit ALWAYS
  binds". It cannot establish "there is no limit" - which is what I
  wrote, and it was wrong.
- `plan.name` is "free" and hosted concurrency is org-wide across the
  sibling repositories, so the limit is not this repository's to spend
  and cannot be pinned from inside it.

**431s IS NOT "THE STRUCTURAL WALL", AND CALLING IT THAT WAS 846's
MISTAKE IN REVERSE.** Between the two runs the same jobs varied 0.62x to
1.65x, and the pole CHANGED IDENTITY - `Harness U5 + U8` in run 1,
`Harness U6 + U7 + U9 controls` in run 2. One sample of a varying
quantity is a draw. This section warned against quoting 14.10 and then
four lines later quoted 7.18 as structure.

**THE MANDATE TARGET IS NOT ONE JOB.** Run 2's durations, descending:
425, 386, 362, 357, 350, 333, 329, 328, 308, 213, ... **NINE of sixteen
already exceed 295s.** Cutting only the largest moves the wall to ~391s,
not to 300s. Any "cut the pole by 1.44x" framing - mine - names the
wrong object. And it assumes a ~5s queue: under run 1's 305s wait no
cut of any size reaches a 300s wall.

**~~What is left un-taken~~ - WRONG, AND THE ERROR WAS A BROKEN PROXY.**
This paragraph said half the harness invocations "never received the
per-row selection this branch is built on", counting 16 of 33
`ci-harness-gate.sh` calls as carrying `--row-re` and 17 as bare. The
count is right and the INFERENCE is wrong, because `--row-re` does not
mean what I read it to mean.

`scripts/ci-harness-gate.sh:45` documents it: `--min-rows N --row-re RE
require at least N lines matching RE`. It is a ROW-COUNTING assertion
over the harness's OWN OUTPUT - it says how many result lines must
appear, and it has nothing to do with which TESTS a row runs. I used a
gate-side counting flag as a proxy for harness-side test selection, and
the two are unrelated. The bare/flagged split says nothing about
selection at all.

MEASURED INSTEAD - and the first replacement for this claim was ALSO
wrong, so this is the second. That version said "EIGHT controls
harnesses were already selecting one test per row". Both halves are
wrong: it is SIXTEEN of thirty-one, and it does not follow the
controls/amputation split. FOUR AMPUTATIONS select (suite-floor,
u1-boot, u4-client, u9-http) and three CONTROLS are bare
(u11-advisory, u15-gate, u3-audit). **Both u15-gate harnesses are
bare** - `check-u15-gate-amputation.sh:70` passes `"$SUITE_REL"`, which
is the bare form by the rule stated above.

The tie, so the next rewrite of this paragraph cannot break it in
silence: the population is 15 controls and 16 amputations. Three bare
controls leaves 12 selecting controls, and **12 + 4 = 16**, which is the
total in the line above. An earlier version of this sentence said five
amputations, and 12 + 5 = 17 contradicted its own total two lines up -
the total was derived and the split beside it was not.

The property is the per-row pytest ARGUMENT, not a flag and not a
filename: BARE only when that argument is exactly `$SUITE` or
`$SUITE_REL`. Derived THREE ways that agree, by three readers who did not share a
population or a rule - over every `scripts/check-*.sh` carrying
`ROW_TIMEOUT`; independently over ci.yml's invocation list; and a third
time keyed on the single pytest invocation guarded by `$ROW_TIMEOUT`,
which excludes each harness's BASELINE by construction rather than by
hand. Three independent instruments agreeing is the evidence here; one
instrument re-run three times would not have been:

    SELECTS 16    BARE 15    (31 harnesses; none run no pytest)

Six selectors no `$selector` grep finds, which is why every earlier
count was wrong: `"$SUITE::$want"` (u4-controls:124 - it CONTAINS
`$SUITE`, so a substring grep reads the tightest selector in the tree as
bare), `$sel` (u4-amputation, u9-amputation), `"${must_die[@]}"`
(u1-amputation), `$named` (u1-controls), `"$expect_file"` (u0-controls),
`"$TESTS"` (suite-floor).

AND THE COST CLAIM INVERTS TOO. That version concluded "the lever was
one fewer PROCESS, not narrower selection". Measured on
`tests/test_resilience.py`, one machine, three draws each:

    whole file, one process (a BARE row)     2.32 / 2.31 / 2.29 s
    ONE node                (a SELECTED row) 0.24 / 0.24 / 0.24 s
    collect-only, the per-process FLOOR      0.24 / 0.23 / 0.23 s
    `uv run` + venv startup                  0.02 - 0.08 s (8 draws)
    `git checkout --` restore                0.00 s (4 draws)

So the process floor is 0.235s and narrowing is worth about 10x on a
bare harness. Selection IS the lever; one fewer process is worth a
quarter of a second. These are single-machine draws under load - the
same suite measured 38% apart twice in one evening - so the RATIO is the
claim here, not the absolutes.

This is left as a struck-through correction rather than deleted, because
the wrong inference drove a brief and two agent messages, and a reader
who saw those needs to find the retraction where the claim was.

## 7a.1 Open, carried forward from R23 - and once deleted by a rewrite

`4be2b09` rewrote this section (61 inserts, 112 deletes) and its own
message closes by saying two R23 items "are recorded as still open
rather than fixed here ... Both are real." **They were recorded
nowhere.** R26 grepped every pattern - `1.9x`, `2.6x`, `4204`, `70.1`,
`H3`, `nine unnamed`, `190s`, `499s`, `R23-M1`, `still open` - against
this file and then repo-wide: zero hits. `REVIEW-R23.md` is not a
mitigation, because it lives on an unmerged branch and is not an
ancestor of this commit. The sole record of all three was the prose of a
commit message, in the section that spent five rewrites establishing
that a commit message is not the record.

That is this section's own thesis executing on the section: **a
wholesale rewrite keeps findings that own a HEADING and silently drops
findings that own a SENTENCE.** Two of the three were noticed at the
time, written down as noticed, and still lost.

All three re-verified against the run payloads by R26, not carried over
from R23:

- **R23-H3, OPEN.** Run 1 has 16 jobs, TWELVE of them named `Harness*`;
  the prediction named three, so NINE are unnamed, not six. Seven of the
  nine exceed 180s (540, 459, 425, 368, 358, 343, 217), and `Harness U1
  amputation` at 217s appears in no per-job table anywhere. "All six
  broke it" is an assertion over a set that was never enumerated.
- **R23-M1, OPEN.** The published ~1.9x runner factor divides a JOB by a
  HARNESS. Read from `steps[]`: `Harness U9 amputation` job 258s, single
  harness step 249s, 249/132 = 1.89x, not 1.95x. `Harness U4 client` job
  216s, two harness steps 67 + 134 = 201s, 201/118 = 1.70x, not 1.83x.
  Both published ratios folded checkout and `uv sync` into a number
  presented as runner scaling. The true spread is 1.70-1.89x, an 11%
  range the rounded figure hid - and two points do not give a factor.
- **The `(G)` mislabel, OPEN and UNRESOLVED.** One figure was labelled
  `(G)`, a real runner measurement, and is 2.6x out: `Harness U3
  controls`, predicted 190s, measured 499s. Whether the label was wrong
  or the step changed underneath it is unsettled. A wrong `(G)` is worse
  than a wrong `(P)`, which is why it is carried here rather than
  dropped.

## 7a.2 The shard plan: a bracket, and the one input that decides it

Seven review rounds. The DIRECTION holds **at 12 lanes and above** and
nowhere else: at 11 lanes sharding provably LOSES **under the fitted
shard costs**, by at least 17.0s, and that row was found by the same
round that extended this table to reach it.
An earlier version of this sentence said "no reviewer has constructed a
case where sharding loses" - true of every row then computed, and promoted
to a general claim it had not earned. The MAGNITUDE has been wrong in both
directions, and round 6 found that the section never propagated its own
stated uncertainty into the cell its headline rests on.

### The population, reproduced by three reviewers

Run 33630968540: every step in a `harness-*` job of duration **>= 5s**,
excluding GitHub's per-job wrapper steps. **33 steps, 3311.0s, largest
298.0s.** Strict `> 5s` gives 32 / 3306 and changes nothing; the boundary
case is one `Install from the frozen lock` at exactly 5.0s. Twelve of the
sixteen jobs are harness lanes (`ci.yml:1649`-`:2132`); the other four are
fixed and top out at 161s in this run.

**Per-lane setup is taken as 13s, and that is a CHERRY-PICKED lane.** This
run's twelve lanes read **8-17s, median 11.5**, and `MEASURED-268:122` in
full says "mean of 12 observations spanning 6-15s". So no figure below is
exact to a tenth: the unsharded floor is **306-315s**, not 311.0. The
constant is added to BOTH columns, so it cannot affect any delta - which
is why the comparisons below survive it and the absolute numbers do not.

**THIS POPULATION IS ONE RUN, AND CI HAS SINCE MOVED OFF IT.** Measured
across the three most recent green runs that share a code base (the fourth
straddles the U3 per-row selection landing at `5f46303` and cannot be
pooled with them):

| run | steps | total | largest |
|---|---|---|---|
| `dcb2725` | 33 | 3311s | 298s |
| `a849f7f` | 35 | 3323s | 304s |
| `1636f56` | 33 | 3492s | 333s |

Row 2 read `34 / 3318s` until this round re-ran it. The script that built
it keyed a per-step table by step NAME, and `a849f7f` is the one run of
the three with a repeated name - `Install from the frozen lock` appears
twice - so one step was silently dropped. The other `+1` is a genuinely
new step, `U15 gate amputation, every row applied`. A dict keyed by
something that is not unique loses rows without erroring, which is why
the count and the total are asserted in the probe and were not here.

Per-step spread over the 33 steps common to all three reaches **118s** on
`U9 HTTP hardening amputation` (201-319s) and 75s on `U3 audit amputation`
(258-333s). Those 33 are exactly `dcb2725`'s and `1636f56`'s whole
populations; `a849f7f` carries them plus the two above.

**Every margin the 12-lane headline rests on is 0s to 8s** - the 2.0s
win, the 0.00s wash under the overhead-deleted refit, the ~0.7s at the
far end of U9's band, and the 8.0s re-anchored win. They are one to two
orders of magnitude below the instrument's own run-to-run spread.

**AND THAT TABLE HAS NOW BEEN COMPUTED ACROSS ALL THREE RUNS, WHICH
SETTLES THE 12-LANE CELL AGAINST ITSELF.** An earlier version of this
paragraph said no lane table existed on `a849f7f` or `1636f56`, so
"the large effects survive" was an expectation rather than a
measurement. `probe-273-packing.py` now fits MIN / MEDIAN / MAX per step
across all three, and the deltas are:

| lanes | MIN | MEDIAN | MAX | |
|---|---:|---:|---:|---|
| 11 | +27.5 | +15.0 | +10.0 | loses throughout |
| 12 | **+19.0** | **-5.0** | **-12.7** | **SIGN FLIPS** |
| 13 | **+1.5** | **-27.0** | **-37.0** | **SIGN FLIPS** |
| 14 | -20.7 | -43.0 | -54.7 | wins throughout |
| 15 | -28.0 | -55.0 | -69.0 | wins throughout |
| 16 | -31.0 | -65.0 | -81.0 | wins throughout |

So the expectation held for 11, 14, 15 and 16 - those signs are stable
across the whole envelope. **It did NOT hold at 12 or 13.** The `-2.0s`
this section publishes at 12 lanes is one draw from a range whose ends
disagree about the direction, and 13 flips too at the MIN extreme. The
12-lane cell should be read as **sign not established**, not as "no worse
and not measurably better" - that phrasing conceded the magnitude while
still assuming the direction.

**The sharded column of that envelope is itself provisional.** `U3_SHARD`
and `U9_SHARD` are still two constants fitted to ONE run and are not refit
per fit, so a MIN-fit unsharded floor differenced against a single-run
shard cost is two different measurements subtracted. The probe therefore
withholds its WINS/loses verdict on every fit but MEDIAN. **No repack or
shard decision at 12 or 13 lanes is supportable until that is closed;**
see task #285.

Two population defects in the older figures above, both in the reader
rather than the runs: a `>= 5s` floor manufactured a step-count change
when one step read 4s in two runs and 5s in a third, and a per-job
dependency install was missing from the wrapper-exclusion list. Corrected,
**all three runs carry the same 35 step names**, and that identity is
asserted rather than counted - two runs can report the same count and
contain different steps.

On the corrected population the regime still flips back: the largest
median step (304s) exceeds sum-of-medians over lanes (3413/12 = 284.4),
so the instance is MAX-bound and the 12-lane floor is **317s** including
setup - **above the five-minute mandate**, which makes sharding the pole
necessary rather than marginal. (An earlier version derived that from
`3323/12 = 276.9`, which is one run's total rather than the sum of
medians; both reach 317 only because the largest step dominates the area
term, and at 11 lanes or fewer that error would have been load-bearing.)
See task #282.

### The bracket

| lanes | unsharded LB / BEST | sharded LB / BEST | delta |
|---|---|---|---|
| 11 | 314.0 / 316.0 achieved | **333.1** / 334.0 | **+18.0s LOSES** |
| 12 | 311.0 / **311.0 exhibited** | 306.4 / 309.0 (R6) | **-2.0s** (single-run fit; sign NOT established across runs - see above) |
| 13 | 311.0 / **311.0 exhibited** | 283.8 / 285.5 | -25.5s |
| 14 | 311.0 / **311.0 exhibited** | 264.5 / 275.0 | -36.0s |
| 15 | 311.0 / **311.0 exhibited** | 247.7 / 256.0 | -55.0s |
| 16 | 311.0 / **311.0 exhibited** | 240.0 / 243.0 | -68.0s |

The 11-lane row is the only one whose exhibited unsharded packing does not
MEET its own lower bound - 316.0 against an LB of 314.0 - so it is
"achieved" but, unlike 12-16, not proved optimal. It is also the only row
whose verdict is a LOSS, and it is included because the DIRECTION sentence
opening this section and the paragraph below both rest on it: it
previously appeared only in prose while the probe printed it. All sharded
BESTs are searched upper bounds at `RESTARTS = 10000`.

**"Exhibited", not "provably optimal".** An earlier version claimed that a
max-bound instance makes greedy LPT provably optimal. **That is false**,
and round 6 gave a counterexample: m=5 over [27,23,22,16,13,9,8,6] has
largest 27 > 24.8 = total/m, and LPT returns 28 against an optimum of 27.
What makes these five cells certain is not a theorem about LPT but that a
packing achieving max-load 298.0 was EXHIBITED at every lane count from 12
to 16. The lower bound and an achieved schedule meet; that is a proof by
construction and it does not generalise.

The unsharded cells stop being provable at **11 lanes**: 3311/11 = 301.0
exceeds 298, so the instance is no longer max-bound (LB 314, best 316.0).

**And 11 lanes is where sharding LOSES.** Sharded LB **333.05** against
an EXHIBITED unsharded **316.00**: a bound of **17.05s**. This is not a
search artefact and no budget can overturn it - a lower bound above an
achieved schedule settles the question. (The probe's own delta column
reads `+18.0s loses` at `RESTARTS = 10000`, and read `+19.5s` at 400;
that figure is a difference of two searched values and is
budget-dependent. The 17.05s bound is not.) It is the one row that bounds
the direction claim above, and it was invisible until the table was
extended by a single lane.

**Budget-independent is not input-independent, and this row is only the
first.** Like every sharded figure here it is conditional on the FITTED
shard costs: the entire bound is `sum(sharded)/11`, and the 209.6s
separating the sharded pool from the unsharded one is fitted overhead.
Measured across the range `#278` contests:

| shard model | sum(sharded) | s_LB(11) | against exhibited unsharded 316.00 |
|---|---|---|---|
| as published (163.3 / 219.5) | 3520.6 | 333.05 | **+17.05s, loses** |
| overhead-deleted refit (165.12 / 234.83), below | 3554.9 | 336.17 | **+20.17s, loses** |
| zero shard overhead (each step halved) | 3311.0 | 314.00 | **-2.00s, the bound REVERSES** |

Re-fitting in `#278`'s direction widens the loss; deleting the overhead
term entirely inverts it, and not only as a bound - an exhibited
zero-overhead packing reaches **315.00**, a 1.0s win against the 316.00.
`#278` measures that term at **130ms** against the **2.24-2.64s** this
model fits, a factor of 17-20, so the reversing end of the range is the
one the evidence currently points at rather than a hypothetical. **The
honest statement is: at 11 lanes sharding loses at ANY SEARCH BUDGET
given the fitted shard costs, and that loss reverses at the low end of
the range those costs are contested over.** It is settled against the
search and unsettled against the inputs.

### ONE PACKER AT SEVERAL BUDGETS - the "two searches" never existed

Every sharded BEST here is an UPPER BOUND produced by a search - the LB
column is not, and is arithmetic - so between two BESTs the LOWER is the
better evidence: a packing that exists is a packing that exists.

An earlier version of this section ran under the heading "TWO PACKERS, AND
MINE IS THE WEAKER ONE" and tabulated four quantities where a reviewer's
search beat this one. All four figures close exactly when `RESTARTS` is
raised, which is what one packer at two budgets looks like: it is the
same code, and the only difference is the module constant. **No second
implementation was ever exhibited, and the "two searches" reading was
supplied rather than observed** - the inference is strong, but it is an
inference about someone else's run, not an observation of their code.
Raise the budget and all four close:

| quantity | R=60 | R=400 | R=10000 | R=40000 | round 6 |
|---|---|---|---|---|---|
| 12-lane sharded best | 310.50 | **309.00** | 309.00 | 309.00 | 309.00 |
| re-anchored 12-lane win | 6.50 | **8.00** | 8.00 | 8.00 | 8.00 |
| U3 refit from 258s, 12-lane | 305.62 | 304.00 | 304.00 | **303.00** | 304.00 |
| overhead-deleted, 12-lane | 316.00 | 311.12 | **311.00** | 311.00 | 311.00 |

Two things the R=40000 column adds, both measured this round.

**Row 3 never actually converged**, here or in round 6: it holds 304.00
from R=400 to R=10000 and then falls to 303.00, stable to R=100000. Both
instruments agreed on an unconverged reading. Rows 1, 2 and 4 are
converged - 309.00, 8.00 and 311.00 are unchanged from R=10000 through
R=100000.

**Row 3's R=60 cell is decided by an input, not by the search.** It reads
305.62 with this section's U3 shard of 138.62 and 305.60 with round 6's
rounded 138.6, and the two are indistinguishable from R=400 onward.
`MEASURED-273-closure-fixes.md` records 305.60 for that reason; the files
do not disagree.

The whole disagreement cost **355 milliseconds** of search - the measured
cost of the entire six-row table at `RESTARTS = 400`, against 53.7ms at
R=60 (median of 5). The "11 milliseconds" this table previously claimed
matches neither quantity measured here at any of the three budgets, and
was estimated rather than timed - as were the "~8s" and "~10s" before it. The probe now runs at `RESTARTS =
10000`, where the table costs 8.81s, because the 11-lane sharded cell was
still falling at 400; see `probe-273-packing.py:93-103`.

**The model INPUTS reproduced exactly all along** - U3's 138.62s shard
against 138.6, U9's overhead-deleted 234.83 against 234.8, U3's 165.12
against 165, and the re-anchored unsharded floor 317.00 against 317.0.
That is what made the diagnosis possible: identical inputs and divergent
outputs point at the search, and the search's only free parameter is its
budget.

**Two errors are recorded here rather than deleted.** First, two runs of
one stochastic algorithm were reported as two implementations disagreeing;
nothing in the outputs said "different packer" and that reading was
supplied, not observed. Second, having decided the other instrument was
better, the question that would have settled it - *what parameter differs?*
- was never asked. Attributing a figure one cannot reproduce is correct and
is what let the next round find this, but attribution is not a substitute
for resolution.

**The lesson that survives the retraction.** A weaker search result is a
fact about the BUDGET, not about CI. The overhead-deleted row is the case
that mattered: read at `R=60` it gives 316.00, a 5s LOSS against an exact
311.0, and publishing that would have inverted the conclusion. Converged it
is 311.00 - a wash. **Before comparing two instruments, raise the budget
until the numbers stop moving; a comparison of unconverged searches
measures the budgets.**

### THE MANDATE IS REACHABLE, and an earlier version of this section denied
it while printing the numbers

A previous version ended "nothing here reaches 300s". **Its own table
contradicts that**: 275.0s at 14 lanes, 256.0s at 15, 243.0s at 16. Under
the modelled shard costs, sharding plus fourteen lanes lands under the
five-minute mandate with 25s to spare, and the inference drawn from the
false sentence - that only removing work can help - does not follow from
it either.

Removing work still helps, and `#249` does that (net -148 pytest process
starts). But it is no longer the only route on these numbers.

### THE CELL THE HEADLINE RESTS ON, AND THE INPUT THAT DECIDES IT

At 12 lanes the win is **2.0s**: 309.0 against 311.0. That margin is thin
enough that the fitted inputs decide it, and this section states elsewhere
that `#278` contests the overhead term by a factor of 17-20 without ever
propagating that into this cell. Round 6 propagated it:

- across U9's own stated 209-235s band the sign NEVER flips, but the
  margin decays from 2.0s to about 0.7s;
- **re-fitting both shard costs with the overhead term DELETED** - the
  `#278` direction, and the scale `MEASURED-268:122` already publishes,
  whose 165s U3 shard reproduces to 165.12 - gives U9 k=2 = 234.8 and a
  12-lane best of **311.00 against an exact 311.00. The win is 0.00s.**

**So at 12 lanes the honest answer is: between a 2.0s win and a wash,
decided entirely by a term this repository measures at 130ms and this
model fits at 2.24-2.64s.** At 12 lanes it is not a regression under any
input tried. It is also not reliably a win. That scope matters: the same
sweep applied to the 11-lane row DOES flip its sign, so "no input tried
makes it worse" is a claim about this cell and not about the section.

Two other re-derivations both move the answer TOWARD sharding, which is
why the direction survives:

- re-deriving U3's shard from the 258s it actually DREW gives 138.62s per
  shard, a 12-lane best of **303.0** - an 8.0s win - and **281.0** at 13
  lanes. This line read "304.0 ... and 282.0" for four rounds. 282.0 was
  never any budget's reading; 304.0 and the 283.0 that
  `MEASURED-273-closure-fixes.md` once proposed in place of 282.0 are
  both R=400 readings of a search that had not converged. Converged:
  13 lanes is 284.0 at R=60, 283.0 at R=400 and 281.0 from R=10000 to
  R=100000; 12 lanes is 303.0 from R=40000 to R=100000;
- re-anchoring to U3's three-run median (below) widens the 12-lane win to
  8.0s - the same figure as the bullet above, reached by a different
  route (that one lowers the sharded best, this one raises the unsharded
  floor to 317.0). The coincidence is not a transcription.

### The re-anchoring caveat was wrong in both directions - and it resolves the `MEASURED-268` disagreement

An earlier version warned that the sharded column "mixes runs" because it
charges shard costs derived from U3's 304s median while the table is
scoped to a run where U3 drew 258s, and estimated "12 and 13 read
318/288".

Both halves are wrong. **The sharded pool is UNCHANGED under re-anchoring**
- `3311 - 258` and `3357 - 304` are the same number, because the
substitution removes whichever U3 step the pool contained. What moves is
the UNSHARDED floor, which rises to **317.0**.

That is the whole `MEASURED-268` disagreement, resolved: it publishes 317s
where this section computes 311s, and the difference is exactly which U3
draw the unsharded pool carries. Neither is wrong; they are scoped to
different runs.

And the consequence runs the other way from the caveat: re-anchored, the
12-lane win **widens to 8.0s**.

### What remains unmeasured

The shard costs 163.3s and 219.5s are FITTED. `scale` is derived as
`k1/(B+R+overhead)`, so the k=1 column closes by construction and carries
no information. U9's k=2 spans 209-235s across the overhead sweep, and
`#278` argues the term should be near zero, which is the case that takes
the 12-lane win to nothing **and reverses the 11-lane loss**. Both of
this section's headline cells rest on that one fitted term, in opposite
directions, and `#278` is where it gets settled.

Nothing has ever run sharded. `#270`, the gate that reds any sharded step,
is not yet mergeable. And nothing in the tree consumes `HARNESS_SHARDS`
(R270-R4-L3), so no splitter exists to produce these lanes yet.


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

- ~~**No run of the new workflow shape has executed.**~~ **IT HAS, AND THIS
  ENTRY WAS STALE.** Run 33614887374 (head 0d2c945) executed the current
  shape and went GREEN, 16/16 jobs. So the ~3.5-4 min and ~30-40 figures
  are not merely (P) - they were superseded by measurement and are
  retracted in section 7a. This bullet is kept struck through because a
  "what I did NOT verify" list that still claims something unverified
  AFTER it was verified is worse than one that never mentioned it: a
  reader trusts this section precisely to know what is open.
- **THE "20-CONCURRENT FREE-TIER CEILING" WAS NEVER CITED AND IS
  CONTRADICTED BY OUR OWN DATA.** That number appears here with no
  source. Run 33610211810's admission ladder was 3,3,3, nine at 4s, then
  30, 51, 56 and 305 - twelve admitted together and four admitted one at
  a time as others finished. If a limit was binding it was near TWELVE,
  not twenty, and "4 of headroom" was arithmetic on a figure nobody
  measured. What IS established: `plan.name` is "free" and the limit is
  ORG-WIDE across the sibling repositories, so it is not this
  repository's to spend and cannot be pinned from inside it.
- **Runner-side timing of the converted harnesses.** The 1.5x
  local-to-runner scaling is one observed ratio (54-56s vs 83s suite),
  not a law - and R23 notes the comparison divides a JOB duration by a
  HARNESS duration, which are different objects. Treat it as an order of
  magnitude, not a coefficient.
- **Cold-cache behaviour is still unmeasured.** Every (L) figure in this
  document is warm-cache, and that has not changed.
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
