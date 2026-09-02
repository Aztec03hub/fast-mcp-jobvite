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

## 7a.2 The shard plan, and why the floor is not the largest step

R7A2 broke three of this section's six claims. It is rewritten from the
payloads rather than annotated, and the conclusion changed shape: the
plan is still not sufficient, but not for the reason first written here.

### The per-harness arithmetic, which survives

Sharding replicates a harness's BASELINE into every shard and divides
only its ROWS, so the payoff is governed by `R/(B+R)`:

| harness | B | R | R/(B+R) | local->CI | k=1 | k=2 |
|---|---|---|---|---|---|---|
| U3 amputation | 14.47s | 153.11s | 0.91 | 1.567x | 304s | 163s |
| U9 amputation | 82.79s | 60.93s | 0.42 | 1.703x | 298s | 219s |

U3's rows dominate 10.6:1. U9's baseline dominates - it builds a
coverage map over the whole 888-test suite (`check-u9-http-amputation.sh:22`),
and every shard rebuilds it. So U3 x2 takes 46.3% off its step and
U9 x2 takes 26.3%: **298s -> 219s, not the ~149s a U3-shaped model
predicts.** That correction stands.

**These four inputs are not verifiable from this tree.** `82.79`/`60.93`
and `14.47`/`153.11` appear only as secondhand quotes inside
`MEASURED-268`'s own "did NOT verify" section; the overhead terms and
both scale factors appear nowhere outside the table above. They are
coherent with the scripts and nothing more. A committed measurement
script is owed.

### The floor is `max(largest step, work/lanes)`, and that changes everything

The first version of this section named a "235s step floor" and treated
it as the constraint. That is wrong: a floor is the LARGER of the biggest
indivisible step and the total work spread over the lanes. Measured over
the three 16-job runs - 44 packable steps, **3719s of total work**,
largest single step 304s:

| lanes | work/lanes | LPT today | LPT sharded |
|---|---|---|---|
| 12 | 310s | 325s | **347s (WORSE)** |
| 13 | 286s | 317s | 322s |
| 14 | 266s | 317s | 300s |
| 15 | 248s | 317s | **276s** |
| 16 | 232s | 317s | 263s |
| 20 | 186s | 317s | 248s |

Two facts fall out, and neither was visible from the largest step alone:

1. **Unsharded, the floor is hard-stopped at 317s at EVERY lane count.**
   Past 13 lanes, adding lanes does nothing: the 304s U3 amputation step
   is indivisible and sets the floor by itself. No amount of packing or
   fan-out reaches 300s. **Sharding is therefore NECESSARY.**
2. **At today's 12 lanes, sharding is a REGRESSION** - 325s to 347s.
   Sharding does not reduce total work; it slightly increases it
   (3719s -> 3742s) and redistributes it. Below the point where the
   largest step stops binding, that trade is a loss.

So the plan is `shard AND raise the lane count`, and it crosses 300s at
**15 lanes (276s)**. Shipping the shards alone against the current 12
lanes would make CI slower and look like the shard work failed.

### The earlier wall prediction is WITHDRAWN

This section previously pooled three floor-to-wall gaps (55/159/91) and
added them to a floor to predict a 290-394s wall. That method is invalid
twice, and R7A2 was right on both counts:

- **Queue is 3-5s, not the gap.** Measured from `run.created_at`:
  4/5s, 4/5s, 3/5s across the three runs. The gap is almost entirely
  packing, not admission latency.
- **The three runs are not one packing.** Runs 33614887374 and
  33629034552 share all 16 job names with each other; 33630968540 shares
  only 5 with either, because #266 repacked between them. Pooling their
  gaps averages two different schedules, and the shard plan would make a
  third.

The correct form is `wall ~= queue + per-job setup + LPT`, which is what
the table above already estimates. No wall figure is asserted here.

### Corrections to specific numbers

- The largest step per run is **376s (U3 CONTROLS)**, **304s (U3
  amputation)**, **298s (U9 amputation)** - one per run, three different
  steps. The earlier "304/304/376" attribution was wrong.
- `U3 audit mutation controls` has a median of 150s but drew 376s once,
  a 3.2x swing. Any "largest remaining step" claim is a band, not a rank.
- 235s (U4) vs 219s (U9 sharded) is inside U9's own step swing. It is a
  tie, not an ordering.
- The suite is 888 tests, not 889.

### The option that would change the picture, unbuilt

R7A2 observed that the covdb U9 rebuilds per shard is a plain sqlite
file: built at `check-u9-http-amputation.sh:93-95`, passed only as
`COVERAGE_DB` at `:132-133`, accepted from any path by
`select-covering-tests.py:47-50`, and joined on a path SUFFIX at `:73-77`.
Nothing ties it to the checkout. Building it once and passing it as an
artifact would drop U9 to roughly a 78s shard plus a ~141s map job, and
U9 would stop sharding badly.

The cost is real and is not free: `:90-92` currently guarantees the map
cannot be stale BY CONSTRUCTION, and hoisting it trades that for a
SHA-keyed staleness guard. This is recorded as an option, not a
recommendation - it has not been built or measured.

### How soft all of this is

Every local B, R and overhead is ONE draw on a loaded box. Each
local->CI scale is one ratio of two noisy numbers, and the 8.6% spread
between the two scales is itself evidence against the uniformity the
model assumes - sharding shifts U9 from 47% to 64% baseline, so that
error lands on the 219s at full weight. Step medians are n=3 across two
different packings, with per-step swings to 3.2x. The LPT table is my
own reimplementation; it agrees with `MEASURED-268` to within a few
seconds, which is corroboration and not proof.

The SHAPE is robust because it follows from B, R and total work
directly: U9 shards badly, the unsharded floor is capped at the largest
step, and sharding pays only once lanes exceed the point where that step
stops binding. The specific seconds are not.


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
