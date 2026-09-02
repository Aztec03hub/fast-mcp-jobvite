# MEASURED: #249, porting R24-H1 (`84d4959`) onto current main

2026-09-02 09:40 AM CDT. Branch `fix/249-port-r24h1`, forked from `main` at
`6f89364`. Worktree `/tmp/w249`. Second revision, after review round 1
(`REVIEW-249.md`, 0C/1H/0M/3L/1N) - see "REVIEW ROUND 1" at the end for what
that round changed and what it corrected in the numbers below.

`84d4959` ("R24-H1: ask the INTACT tree once per harness, because no mutated run
can answer the question") was written, reviewed, credited as done on task #249 -
and never landed. `git for-each-ref --contains 84d4959` returns one ref,
`refs/heads/ci/242-under-five`, which is not an ancestor of main. Eight harnesses
still carry the defect it fixes.

## WHAT THE DEFECT IS ON MAIN, WHICH IS NOT WHAT IT WAS ON `84d4959`'S BASE

This is the first thing a reader needs, because the two trees carry DIFFERENT
wrong answers to the same question and a cherry-pick would have swapped one for
the other blind.

`84d4959` forked before #244. On its base, the per-row `--collect-only` probe had
already been deleted by #244 and replaced by a per-row rule reading pytest's rc
plus its `^ERROR <file> - <Exception>` line; `84d4959` deleted THAT rule.

Main never took #244. On main the operative code is the ORIGINAL per-row probe,
a second pytest process inside `mutate()`:

    main:scripts/check-u9-http-controls.sh:119
      timeout "$SELECTOR_TIMEOUT" uv run --frozen pytest "$selector" \
        --collect-only -q -p no:cacheprovider >/dev/null 2>&1

So on main the fix does more than it did on the branch it was written on. It is
still the correctness fix - the property is about the INTACT tree and `mutate()`
is a loop over MUTATED ones - and here it also DELETES a pytest process per row
instead of merely relocating a grep.

`git cherry-pick 84d4959` was NOT used, and could not have been: it would have
tried to remove a block that is not in main's files, and where it did apply it
would have reverted main's ROW_FLOOR derivation prose (rewritten since the fork -
see "Differences from `84d4959`" below).

## THE TRANSFORMATION

Applied to all eight, anchored on lines asserted UNIQUE per file before use
(`/tmp/w249-port.py`; it exits non-zero on a missing or duplicated anchor rather
than editing on a guess):

1. after `TOTAL=0` - declare `SELECTORS=()`
2. after `TOTAL=$((TOTAL + 1))` in `mutate()` - `SELECTORS+=("$selector")`,
   placed beside the counter it must equal
3. DELETE the per-row probe block from `mutate()` (comment head
   `# DOES THE SELECTOR STILL RESOLVE?` through the closing `fi` of its `if`,
   plus the separating blank line)
4. after `ROW_FLOOR=N`, before `harness_result_ran` - the ONE intact-tree check:
   a guard that refuses at zero rows or on a count mismatch, then a single
   `timeout "$SELECTOR_TIMEOUT" uv run --frozen pytest "${SELECTORS[@]}"
   --collect-only`, then a success line

The check sits BEFORE `harness_result_ran`, deliberately. `harness_result_emit`
defaults `status` to `refused` when `harness_result_ran` was never called, so an
`exit 3` here prints `status=refused` - the honest word for a harness that cannot
aim - rather than `breach`, which would read as a mutation result.

Aggregate check that nothing else was touched: every deleted line across the
eight is one of the 14 lines of that probe block, each appearing exactly 8 times,
plus the per-file comment prose above it. Nothing else was removed. Re-derived
independently by the reviewer (`REVIEW-249.md` D4).

Deleted process starts: the eight declared ROW_FLOORs sum to 12+21+17+20+16+31+
25+14 = **156**. Eight one-per-harness calls are added. Net **-148 pytest process
starts** per full harness sweep.

### Per-harness notes

All eight took the transformation identically - the deleted block's CODE is
byte-identical in all eight (only the explanatory comment above it differs), and
all four anchors were unique in every file. **Nothing was left unported.**

One ordering note, `check-u7-resilience-controls.sh`. Alone among the eight, u7
prints `echo "$FIRED/$TOTAL controls fired."` and calls `harness_result_tally`
BEFORE `ROW_FLOOR=31` (lines 535-538), where the other seven print them after.
The new block therefore emits its refusal AFTER u7's "31/31 controls fired."
line. This is cosmetically inverted but not wrong: `harness_result_ran` is still
below the new block, so a refusal still exits 3 with `status=refused`, and the
tally field is independent of status by design (see the "WHY THIS IS NOT JUST
`status` READ TWICE" note in `scripts/lib/harness-result.sh`). The reviewer read
`:525`-`:640` and confirmed nothing between the last `mutate` and the new block
can exit, so the check cannot be skipped on a completing run.

## DIFFERENCES FROM `84d4959`, AND WHY

Measured file by file. **Method, stated exactly so a re-runner gets the published
number** (N1): `git show 84d4959:scripts/<f> | diff -u - scripts/<f> |
grep -cE '^[-+]'`, RAW, including whitespace-only changes, less the two diff
headers. `/tmp/w249-n1.sh` reproduces it.

| file | changed lines vs `84d4959` |
|---|---|
| check-u9-http-controls.sh | 73 |
| check-u10-write / u12-jobfeed / u14-arguments / u8-candidates | 89 each |
| check-body-cap / u5-jobs | 99 each |
| check-u7-resilience | 113 |

(The first revision of this doc published 52/68/78/90. Those silently excluded
whitespace-only pairs while claiming the plain `diff -u` method, which is why
the reviewer could not reproduce them - N1. The figures above are the raw counts
under the stated method, and they are also larger because review round 1 added
the L1 and L2 code below.)

Every difference falls into one of five buckets.

1. **The ROW_FLOOR derivation comments (all files except u9).** Main rewrote
   these since the fork. The port keeps MAIN's version; `84d4959`'s file carries
   the older prose. Keeping the branch's would have been the silent revert a
   cherry-pick produces. This is the whole reason for buckets existing at all.

2. **The `harness_result_tally` position in u7.** Main moved it above the floor
   comment; `84d4959` has it below. Main's position is kept - the port inserted
   nothing there.

3. **The rc=124 branch, KEPT from main and absent from `84d4959`.** `84d4959`
   wrote the call as `if ! timeout ...; then`, which discards the exit code, so a
   collection HANG and a rename render identically. Main's per-row probe
   distinguished them ("collection NEVER FINISHED... a hang, not a rename") and
   this port preserves that by capturing `sel_rc` and branching on 124. Two
   reasons: (a) losing a diagnosis main already has would be a regression smuggled
   in under a port, and (b) `scripts/check-timeout-literals.py` requires a seconds
   figure in an abort message to be INTERPOLATED from the bound's name - the
   preserved branch is where `${SELECTOR_TIMEOUT}s` is read, and it keeps that
   gate meaningful rather than merely satisfied by absence. The reviewer drove
   this branch with a REAL firing `timeout` (`SELECTOR_TIMEOUT=0.01`), not by
   reading the `if`, and it printed the hang message.

4. **Prose in the new block's comment, and one added success line.** The comment
   is rewritten because it must describe MAIN's starting point (the per-row pytest
   probe), not `84d4959`'s (#244's grep rule); describing the wrong predecessor
   would be a doc that lies at exit 0. `84d4959`'s measured per-harness misreport
   counts (u7 31/31, u8 14/25, u12 2/17, u5 2/16) were dropped rather than copied
   forward, because those were measured against #244's rule which is NOT in this
   tree - a number carried into a tree it was not measured on is a second copy
   free to disagree with reality. The added
   `########## ALL $TOTAL SELECTORS RESOLVE (one intact-tree process)` follows
   `check-u3-audit-controls.sh`'s shape on main, so a switched-off check and a
   passing one do not render identically. It does not match any `--row-re` in
   `ci.yml` (`^########## M[0-9]+ `), so no row count moves; the reviewer went
   further and checked `ci-harness-gate.sh:90` initialises `row_re=""` with no
   default and `:416`-`:418` counts rows only when `--min-rows` is passed, so
   there is no implicit `^########## ` counter anywhere for the line to inflate.

5. **The L1 and L2 code added in review round 1** (the zero-row guard and the
   two-line pointer in the failure branch). Neither is in `84d4959`. L2 fixes a
   defect this port introduced on its own; see below.

No unexplained difference remains.

The reference for "what fixed looks like against CURRENT main" was
`scripts/check-u3-audit-controls.sh`, which carries this shape already - arrived
at from the other direction by #252's per-row selection work (`5f46303`), and
citing `84d4959` by hash in its own comment at line 95.

## MEASURED

### Before/after verdicts - four harnesses, full unfiltered stdout

Run on `main` (`6f89364`) and on the ported tree. The comparison is a `diff` of
the WHOLE stdout, not a grep of selected line shapes - a formatting change hiding
a verdict change was the thing to rule out, and a grep of shapes cannot see it.

| harness | rows | reps | differing lines, whole stdout | verdict moved? |
|---|---|---|---|---|
| check-u9-http-controls.sh | 14 | 2 | pytest duration + 1 added success line | NO |
| check-body-cap-controls.sh | 12 | 2 | pytest duration + 1 added success line | NO |
| check-u5-jobs-controls.sh | 16 | 2 | pytest duration + 1 added success line | NO |
| check-u12-jobfeed-controls.sh | 17 | 2 | pytest duration + 1 added success line | NO |

All `HARNESS-RESULT` lines byte-identical between arms. **No verdict moved on any
of the four.** u5-jobs and u12-jobfeed were closed by the reviewer, not by me;
u9 and body-cap I ran in both states, and re-ran after the L1/L2 fixes with the
same result:

    check-u9-http-controls.sh    rc=0  rows=14 floor=14 fired=14/14 status=ok
    check-body-cap-controls.sh   rc=0  rows=12 floor=12 fired=12/12 status=ok

### The other four, after only

`check-u7-resilience`, `check-u8-candidates`, `check-u10-write` and
`check-u14-arguments` were run in the ported state ONLY. Nobody has run them
before/after. This is a floor check, not a verdict comparison:

    check-u7-resilience-controls.sh  rc=0  fired=31/31  status=ok
    check-u8-candidates-controls.sh  rc=0  fired=25/25  status=ok
    check-u10-write-controls.sh      rc=0  fired=21/21  status=ok
    check-u14-arguments-controls.sh  rc=0  fired=20/20  status=ok

`docs/reviews/check-row-floor-exactness.py` asserts every floor EQUALS its
harness's live row count, and all four printed exactly their floor. Given the
byte-identical transformation and four clean before/after comparisons, the
residual risk is low - but it is not zero, and it is stated here rather than
implied away.

### A renamed selector is STILL DETECTED - the fix must not trade a defect for a blind spot

Negative control (`/tmp/w249-planted.sh`): one selector renamed to a test that
does not exist (`test_a_malformed_inbound_request_id_is_REPLACED_XYZ`), planted
into a COPY of the u9 harness, run against both shapes. The reviewer reproduced
this independently with a different renamed selector.

| shape | rc | what it printed |
|---|---|---|
| main (per-row probe) | 1 | `SELECTOR DOES NOT RESOLVE - the test was renamed or moved.` / `fired=13/14 status=breach` |
| ported (one per harness) | 3 | `A SELECTOR DOES NOT RESOLVE ON THE INTACT TREE (pytest rc=4).` / `rows=0 floor=0 status=refused` |

Still caught, and the overall verdict is caught LOUDER: `refused` instead of
`breach`, which is the correct word - the harness could not aim, it did not
measure a control and find it short.

**AT THE ROW, HOWEVER, IT IS NOW CAUGHT SILENTLY, AND THAT IS A REAL LOSS**
(R249-L1). Main's per-row probe printed, on the offending row itself,
`SELECTOR DOES NOT RESOLVE - the test was renamed or moved.` Under the port that
row instead runs the mutation, gets a non-zero rc from a selector matching
nothing, and prints `KILLED - the named test went red, as it must` - a positive
verdict it did not earn. Only the end-of-harness block refuses, and its message
names no row. The selector IS recoverable, because pytest's `tail -20` prints
`ERROR: not found: <nodeid>`, but only if the reader knows to distrust a `KILLED`
line printed forty lines earlier. Review round 1 added two lines to the failure
branch of all eight, pointing the reader at exactly that:

    Any row above whose target appears in those ERROR lines printed a
    verdict it did not earn - read the target, not the verdict.

Verified firing: the planted-rename control now ends with those two lines
immediately below pytest's `ERROR: not found:` line. Per-row attribution is the
one thing this port loses; the end-of-harness refusal plus this pointer is the
compensating control, and `tail -20` can still truncate if several selectors are
missing at once.

### Timing

**Superseding the first revision's n=1 table** (R249-L3). These are the
reviewer's re-measurements: A/B **interleaved** (base, ported, base, ported) so
drift on a shared box hits both arms equally, both worktree venvs warmed before
the first timed run, sequential throughout because `$OUT` is a fixed `/tmp` path
shared between worktrees. Medians, with the observed range beside them.

| harness | rows | main (s) | ported (s) | median delta | per row |
|---|---|---|---|---|---|
| check-u9-http-controls.sh | 14 | 67.1 / 68.3 / 67.7 → **67.7** | 39.0 / 43.3 / 40.0 → **40.0** | **-27.7s (-40.9%)** | -1.98s |
| check-body-cap-controls.sh | 12 | 58.1 / 55.5 / 58.6 → **58.1** | 34.7 / 34.2 / 34.9 → **34.7** | **-23.4s (-40.3%)** | -1.95s |
| check-u5-jobs-controls.sh | 16 | 71.6 / 70.7 → **71.2** | 44.5 / 39.8 → **42.2** | **-29.0s (-40.8%)** | -1.81s |
| check-u12-jobfeed-controls.sh | 17 | 75.3 / 76.4 → **75.9** | 47.9 / 44.7 → **46.3** | **-29.6s (-39.0%)** | -1.74s |

Spread, since a median alone hides it: the base arm is tight (u9 1.2s, body-cap
3.1s, u5 0.9s, u12 1.1s across reps); the ported arm is tight on three and
noisier on u9 (39.0-43.3, 4.3s). The smallest observed win on any pair of samples
is -23.4s and **the direction never inverts on any rep**. Load on the box was
2.4-3.3 throughout with other agents live; interleaving controls for drift
between the arms, but these absolute seconds are not portable to a GitHub runner.

My own first-revision figures were n=1, back to back, and are superseded in both
directions: u9's -42.6% was about 1.7 points flattered by a high `before`, and
**body-cap's -34.9% UNDERSTATED the win, which is really -40.3%**.

Per row is **1.74-1.98s**, one `uv run --frozen pytest` startup and collection.
The first revision offered 1.7-2.1s; 2.1 does not appear in the data.

    Extrapolated over the 156 rows of the eight, that is on the order of 4.5-5.1
    minutes of pytest startup deleted from a full sweep. That is RUNNER WORK, not
    wall clock: REVAMP-238-ci.md:495-556 measures the floor as
    `max(slowest fixed job, LPT over harness steps)`, and at today's 12 lanes it
    is 311s, set alone by the indivisible 298s U9 AMPUTATION step this branch
    does not touch. Removing 300s from the packable side moves the LPT term from
    289s to 264s and the floor not at all. The gain is banked for the 14-lane
    sharded target, and shows up as CPU now. #273 should take the measured
    per-row figure above rather than the row count.

That paragraph replaces a first-revision claim that "CI's floor is bound by TOTAL
work spread over lanes rather than by the largest step - so this is work removed,
not work moved." That was false in this tree and would have had #273 book 4.5-5.5
minutes of wall clock that will not arrive. It came from the dispatching brief
and I carried it without checking it against `REVAMP-238-ci.md`, which is an
ancestor of this very commit (`git merge-base --is-ancestor 96072cd ecb37b4` →
true) and measures it the other way. **Grep the design before repeating a
premise, including one you were handed.**

Checked, not copied: `REVAMP-238-ci.md:520` gives harness work 3311s over 12
lanes; 3311/12 = 275.9, +13s setup = 289s. Ported, 3011/12 = 250.9, +13s = 264s.
Both are perfect-packing lower bounds rather than a greedy LPT figure, so the
true term sits at or above them - which does not move the conclusion, because
`298 + 13 = 311` binds above both in either column. `git diff --name-only
6f89364 ecb37b4` touches zero `*-amputation.sh` files, so the 298s step is
untouched under any model.

## GATES

Run in `/tmp/w249` with ci.yml's exact invocations, flags included, and re-run
after the L1/L2 fixes.

    shellcheck --severity=warning <the 8 files>                            rc=0
    bash -n <the 8 files>                                            8x    rc=0
    uv run --frozen python scripts/check-timeout-literals.py --self-test   rc=0
    uv run --frozen python scripts/check-timeout-literals.py               rc=0
    python3 scripts/check-harness-anchors.py --self-check --floor 464      rc=0
    python3 docs/reviews/check-row-floors.py                               rc=0
    python3 docs/reviews/check-row-floor-exactness.py                      rc=0
    python3 docs/reviews/check-row-floor-exactness.py --self-test          rc=0  (A1-A20 all PASS)
    bash scripts/check-pytest-bounded.sh --self-test                       rc=0
    bash scripts/check-pytest-bounded.sh                                   rc=0  (81 invocations, 81 bounded)
    bash docs/reviews/check-brief-report-refs-controls.sh                  rc=0
    python3 docs/reviews/check-design-citations.py                         rc=0
    python3 scripts/check-committed-file-types.py --all                    rc=0

    bash scripts/ci-harness-gate.sh check-u9-http-controls.sh --controls-fired   rc=0
    bash scripts/ci-harness-gate.sh check-body-cap-controls.sh \
      --controls-fired --min-rows 12 --row-re '^########## M[0-9]+ '             rc=0

No floor moved: `check-row-floor-exactness.py` prints "Every floor equals its
harness's live row count" over 34 harnesses, 16 `--min-rows` values compared to
live counts.

**A GREEN LICENSES ONLY WHAT IT CHECKED, and one of these greens checks less than
it looks like it does.** `check-pytest-bounded.sh` reports **81 invocations, 81
bounded on main AND on this branch** - the port deletes 8 per-row calls and adds
8, so the count is identical and that gate CANNOT DISTINGUISH THE TWO TREES. It
verifies the new call is bounded, which is what it exists for. It is not evidence
that the port happened. Found by the reviewer; recorded here because a gate that
cannot see a change should never be cited as having approved it.

Out of scope but recorded, because a silent red is worse than a noisy one:
`docs/reviews/check-review-coverage.py` exits 1 on this branch AND on `6f89364`.
It is **pre-existing on main and not caused by this port**.

## REVIEW ROUND 1

`REVIEW-249.md` @ `ecb37b4`: 0 Critical, 1 High, 0 Medium, 3 Low, 1 Nit. The
reviewer found nothing to change in the eight script changes themselves; the
blocker was this document.

| id | finding | what changed |
|---|---|---|
| H1 | The value claim was refuted by an ancestor of this commit: at 12 lanes the port removes ZERO wall clock | Timing conclusion rewritten to the reviewer's paragraph, arithmetic re-checked against `REVAMP-238-ci.md:495-556` rather than against the summary |
| L1 | A renamed selector's own row now prints `KILLED`; the doc claimed only "caught LOUDER" | Two pointer lines added to the failure branch of all eight; the loss recorded above in full |
| L2 | The new guard was VACUOUS at `TOTAL=0` - it printed a success line for a check that checked nothing | `[ "$TOTAL" -eq 0 ] \|\|` restored in all eight, the guard `check-u3-audit-controls.sh:461` has and this port dropped |
| L3 | Timing was n=1 per cell with no spread | Table replaced with n>=2 interleaved medians and ranges |
| N1 | Changed-line counts were 4-6 low against the stated method | Raw counts published, method stated exactly |

**L2 was the port's own defect, not one inherited**, and it was proved by
AMPUTATION rather than by reading the `if` (`/tmp/w249-l2probe.sh` rewrites every
`mutate` call site to `false && mutate`, so `mutate` is never called and no row
runs):

    BEFORE the fix   rc=1  "########## ALL 0 SELECTORS RESOLVE (one intact-tree process)"
                           rows=0 floor=14 status=breach
    AFTER  the fix   rc=3  "########## RECORDED 0 SELECTORS FOR 0 ROWS."
                           rows=0 floor=0 status=refused

The pre-fix run still failed overall - `TOTAL -lt ROW_FLOOR` exits 1 two lines
later - which is why this is Low. But it announced a passing check first, which
is the exact shape ("a green that tested nothing") these harnesses exist to
find.

## WHAT I DID NOT DO, AND WHAT NOBODY HAS DONE

* Did not push, did not merge, did not touch `ci/242-under-five` or any other
  agent's worktree. No escalation was granted or requested; the coordinator
  stated plainly that it could not grant any, and none was taken.
* **Before/after verdict comparison on four of the eight** - `u7-resilience`,
  `u8-candidates`, `u10-write`, `u14-arguments`. They are ported-only in every
  record that exists. Four of the eight were compared (two by me, two by the
  reviewer).
* Did not run CI. H1's arithmetic is carried through `REVAMP-238-ci.md`'s model
  and its n=1 run 33630968540, which that document itself flags as n=1. If the
  model is wrong the magnitude moves; the direction does not, because the 298s
  step is untouched.
* `src/fast_mcp_jobvite/*.py` is MUTATED IN PLACE by these harnesses and restored
  per row, so `git status` in this worktree shows product code as modified WHILE
  a harness is running. It is transient by design (each row `cmp`s the restored
  file against a pristine copy and exits 3 if it differs). Verified clean after
  the runs three ways, because `git diff --quiet` alone is blind to an untracked
  file: `git diff --quiet -- src/` rc=0, `git status --porcelain -- src/` 0
  lines, and a byte `cmp` of the working file against `HEAD:`. No product code is
  in this branch.
