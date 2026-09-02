# REPACK-244: the queue was transient, and one step is the whole remaining miss

Task #244, branch `ci/242-under-five`, worktree
`/home/plafayette/claude_projects/evolv/fmj-worktrees/w244`. Branched off `5cca9eb`; `main` merged in at `0ca2eec`, which contains
`d55fa74`, `0d2c945` and `6894e50` (each verified with
`git merge-base --is-ancestor <sha> HEAD`). Local `main` has since moved to
`7431bb50`, which this branch does NOT contain - so every figure below is
as at `0ca2eec`.

Phil, verbatim: "FULL CI IS NOT TO TAKE MORE THAN 5 MINS WHEN REVAMP IS
DONE." Full CI means every check on every trigger, nothing gated away,
nothing moved off the push path. Nothing below deletes a check.

**(G)** = read from the GitHub API. **(L)** = measured locally this session.
**(P)** = a prediction. **This branch has not been pushed, so no wall-clock
figure for the new shape is a measurement.**

---

## 1. THE QUEUE GAP WAS TRANSIENT - and my first answer to this was WRONG

I first reported that this organisation's observed runner capacity was 12
concurrent jobs, and built the fan-out around that. **That conclusion is
withdrawn.** A second run refutes it, and I verified it from the API myself
rather than taking it on report:

    run           wall   pole   gap   maxQ   jobs starting within 10s
    33610211810    845    540   305    305   12 of 16
    33614887374    430    425     5      5   16 of 16

`gap` is wall minus the longest single job; `maxQ` is the largest per-job
queue wait. **maxQ tracks gap almost exactly in both runs.** So the 306s that
REVAMP-238 §7 could not account for was runner availability on one occasion,
not a structural ceiling: the same 16 jobs all got runners within 5 seconds
the second time.

What I got wrong, precisely: I had n=1 and I said so, but I still let a
single draw name a "ceiling", and I sized the fan-out against it. The
org-wide Free-plan limit is real and shared with ~100 sibling repositories -
that part stands - but **we have not hit it**, and one bad draw is not a
measurement of where it is. Two draws are not either. Treat headroom as
UNMEASURED in both directions.

**The real structural baseline is 430s = 7.18 min**, not 14.10 min. About
five minutes of the original figure was queue that did not reproduce.

## 2. WHAT THE BRIEF GOT WRONG, AND WHAT I GOT WRONG

- **"Rebalancing alone cannot meet the mandate" - HOLDS, for a different
  reason than the brief gave.** The brief argued from the average (3869s over
  12 jobs is ~322s). The binding constraint is not the average, it is the
  **largest single step**, because a step cannot be split across runners.
- **Lever (d), #241's single `--cov` run, IS ALREADY SPENT.** It landed in
  `620407f`, on `main`, and is inside both measured runs.
- **Lever (a) rested on a proxy that does not measure what it was read as.**
  REVAMP-238 §7 read "17 of 33 calls are bare `--row-re`" as "17 never got
  per-row selection". `--row-re` is a row-COUNTING flag. Read the harnesses
  instead: eight controls harnesses were already selecting one test per row
  all along, and in those eight the cost was never test execution (§3).
- **My own "capacity is 12" - WITHDRAWN, see §1.**

## 3. WHAT THE COST ACTUALLY IS

Measured (L):

    whole 3-file U3 suite            9.28s
    same suite, `-k <one test>`      0.24s
    one test file, collect-only      1.10s
    `uv run --frozen` overhead       0.02s   <- I expected a per-row tax. There is none.

Once a row already runs one test, what is left is process startup and
collection, ~1s per pytest invocation. Those eight harnesses were starting
**two** pytest processes per row: a `--collect-only` pre-flight on the intact
tree, then the real run. The lever is one fewer process, not narrower
selection.

## 4. WHAT CHANGED

### U3 controls: whole suite per row -> `-k "$want"`

It ran the whole three-file `$SUITE` for each of 15 rows to answer a question
its own verdict has always narrowed to one named test.

`-k` rather than a `::` node id, because M7's `test_arm3` and M11's
`test_case2` each name three tests deliberately. My first version derived the
defining file by grep and demanded exactly one match; it reported those two
rows as unlocatable, which is how I learned they were prefixes, not
truncations.

The verdict was `grep -q "$want"` over the whole output, **unanchored**. It is
now the anchored `FAILED` line for a node whose test name starts with
`$want`. **AMPUTATION, run both ways:** with `$want` set to `tests` - a string
in every FAILED line's PATH and not a test name at all - the **pre-fix code
exits 0 and prints "15 killed, 0 not killed, status=ok"**. A complete false
green. The new code exits 1.

### The `--collect-only` pre-flight, deleted in eight harnesses

The property it bought - "the named test still exists, so a rename cannot
report KILLED forever while testing nothing" - is kept. The second process is
gone.

**My first rule for it was wrong, and U14 caught it.** I read pytest rc 4 or 5
as "the selector did not resolve". But U14's M7 mutates `GetJobFeedInput` onto
an undefined base, the module fails to import, and pytest exits 4 for that too
- a real kill, reported as a broken harness. Measured, three ways:

    absent node id          rc=4   `ERROR: not found: <path>`
    `-k` matching nothing   rc=5   "N deselected"
    mutation breaks import  rc=4   `ERROR: found no collectors for ...`
                                   AND `ERROR <file> - NameError: ...`

The discriminator is the collection-error line, not the exit code.

### The fan-out, re-packed by measured cost: 16 jobs -> 12

All 76 gate invocations are **byte-identical** to `main`'s (the parsed `run:`
bodies diff empty). The only step-count change is 15 `Install uv` / `Install
from the frozen lock` pairs becoming 11.

## 5. THE ARITHMETIC, RE-DERIVED AGAINST THE CLEAN-QUEUE RUN

Local before/after, **same box, same session, back to back**: `main` at
`0ca2eec` in one worktree, this branch in another. No modelling.

    step    localB  localA   runnerB  ratio  runnerA(P)  saved
    u3c        270      15       376   1.39          21    355
    u8c        115      34       130   1.13          38     92
    u10c        97      30       127   1.31          39     88
    u12c        83      26       105   1.27          33     72
    u5c         73      25        87   1.19          30     57
    u14c        71      25       133   1.87          47     86
    u9c         69      22       123   1.78          39     84
    u7c         53      22       102   1.92          42     60
    bcapc       58      23       101   1.74          40     61
    TOTAL      889     222      1284               329    955

### The scaling method I used FIRST, and withdrew

My first version of this report scaled every changed step by ONE factor,
x3.54, taken as the worst of four harnesses I had not changed, measured
against run 33610211810:

    check-u5-jobs-amputation.sh          24s (L) ->  85s (G)   x3.54
    check-u3-audit-amputation.sh        124s (L) -> 332s (G)   x2.68
    check-critical-coverage-amputation   87s (L) -> 215s (G)   x2.47
    check-u9-http-amputation.sh         141s (L) -> 249s (G)   x1.77

I noted at the time that x2.7 would have landed ~296s and MET the mandate,
and declined to claim it. That was the right call for the wrong reason: the
problem is not which of the four to pick, it is that **a single factor is the
wrong instrument**. It is the same error REVAMP-238 made with a flat 1.5x,
and I reproduced it in the opposite direction. The four ratios in THIS block
are superseded by the nine per-step ratios in the table ABOVE them, and are
kept only so the spread is in the record.

`runnerB` is that step in run 33614887374 (G). Each step is scaled by **its
own** ratio, not one global factor - the ratios span 1.13x to 1.92x and no
single number would do. That is the method REVAMP-238 got wrong when it
applied a flat 1.5x to everything.

    harness lane   3477s (G) -> 2522s (P)
    LARGEST SINGLE STEP: check-u3-audit-amputation.sh, 317s (G)

Bin-packing the lane, LPT by measured cost:

     6 lanes -> pole 427s   wall(P) 444s   [10 jobs]
     8 lanes -> pole 320s   wall(P) 337s   [12 jobs]
    10 lanes -> pole 317s   wall(P) 334s   [14 jobs]
    12 lanes -> pole 317s   wall(P) 334s   [16 jobs]
    14 lanes -> pole 317s   wall(P) 334s   [18 jobs]

wall(P) = 5s queue + ~12s checkout/uv/sync + pole.

**Eight lanes is already at the floor.** Ten, twelve and fourteen lanes all
give the same 317s pole, because one step sets it. So lever (c), widening the
fan-out, is worth **three seconds** here - not because of a ceiling, which is
what I wrongly said first, but because U3's amputation is longer than any lane
would be. Twelve jobs is also the shape that survived the bad draw, so it is
the lower-variance choice for free.

    WALL (P) = ~337s = 5.6 min   against 430s = 7.18 min structural (G)

**MISSES the mandate by 1.12x.**

### Verify it with

    ID=<the run id for this branch's first push>
    gh api "repos/:owner/:repo/actions/runs/$ID" --jq '{run_started_at, head_sha}'
    gh api "repos/:owner/:repo/actions/runs/$ID/jobs?per_page=100" --jq \
      '.jobs[] | {name, started_at, completed_at}'

Wall is `max(completed_at) - run_started_at`. Per job, `started_at` minus
`run_started_at` is the queue wait. Not `gh run view --json jobs` - no step
timestamps.

## 6. WHAT IS LEFT, AND IT IS TWO STEPS

To clear a 300s wall every step must be under roughly 283s. Two are not:

    check-u3-audit-amputation.sh   317s (G)
    check-u9-http-amputation.sh    300s (G)

Everything else is 235s or below.

**U3's amputation cannot take the selection its controls file just took, and
this is a refusal with a reason.** U3 controls asks "did the NAMED test
notice", so running only that test asks the identical question. U3
amputation's PRODUCT is its survivor list - every assertion that still
reported success against the amputated tree, printed for a human to read and
explain. Its own closing line says so: "Survivors are the OUTPUT. Read each
one and say why it survived." Narrowing to the covering set shrinks that
population by construction, and the report would say less while CI stayed
green, because the gate reads `rows=` and `applied=`, not survivors. That is a
green gate quietly no longer covering what it used to.

**U9's amputation is the sharper finding: it ALREADY has coverage-map
selection** - it is one of #238's converted five - and it still costs 300s,
up from 249s in the earlier run. The selection lever is spent there. Whatever
makes that step cheap is not selection.

So the mandate needs a decision about what those two harnesses are for, which
is Tier 0's call and not mine to take inside a performance task.

## 6a. R23's RUN-2 POLE - the number is right, the category is not

R23 measured that run 33614887374's pole job, `Harness U6 + U7 + U9
controls` (425s), carries 288s of invocations with no `--row-re`. I
re-derived it: u6 controls 45 + u6 amputation 18 + u7 controls 102 + u9
controls 123 = 288. **The arithmetic is confirmed.**

**The inference it invites is the one Tier 0 has just retracted.** `--row-re`
is a row-COUNTING assertion; it does not say which tests a row runs. Split
that same 288s by what the harnesses actually do:

    u7-resilience-controls   102s   ALREADY selected per row
    u9-http-controls         123s   ALREADY selected per row
    u6-paging-controls        45s   genuinely unconverted
    u6-paging-amputation      18s   genuinely unconverted

    already selected: 225s of 288 (78%)
    genuinely bare:    63s of 288 (22%)

So 78% of R23's block was never a selection gap. Reading it as one would be
the third time this proxy has misled a reader today. **The honest residual is
63s, and it is the two harnesses §7 already names** as still carrying the
pre-flight.

The pole itself does dissolve, but through the pre-flight removal rather than
through selection:

    step   run 2   after #244
    u6c       45      45   still has the pre-flight
    u6a       18      18   still has the pre-flight
    u7c      102      42   CUT
    u9c      123      39   CUT
    u7a      124     124   amputation, untouched
    TOTAL    412     268

That is the useful form of R23's finding: my change takes 157s off the job
that was the pole in the only clean-queue run we have.

## 7. WHAT I DID NOT VERIFY

- **No run of this shape has executed.** Every figure in §5 marked (P) is a
  prediction; the first push is the positive control.
- **Per-step runner costs are NOISY between runs**, which weakens every
  prediction built on one run: U4 client amputation 134s -> 235s, U9
  amputation 249s -> 300s, U8 controls 214s -> 130s, U3 controls 488s ->
  376s across the two runs. I used the clean-queue run throughout, but a
  third run would move these numbers again.
- **Headroom is unmeasured in both directions.** Two draws, one queued badly
  and one not at all. Neither proves where the org-wide limit is.
- **The rename control is now run on all eight** pre-flight-removed
  harnesses, each caught with rc=1 and exactly one row down (u8 24/25, u5
  15/16, u12 16/17, u9 13/14, u10 20/21, u14 19/20, u7 30/31, body-cap
  11/12). What is proved on **u8 only** is the comparison against the
  PRE-FIX code, which caught the same rename identically - so "the property
  is unchanged" rests on one harness, and "the property still fires" rests
  on eight.
- **`check-u1-boot-controls.sh` and `check-u6-paging-controls.sh` still carry
  the pre-flight.** Their verdict blocks have a different shape. 165s and 45s
  (G); neither is on the critical path.
- **REVAMP-238 §7 is left alone** - Tier 0 is rewriting it, and citations
  there are as-at acceptance (ec57a65).
