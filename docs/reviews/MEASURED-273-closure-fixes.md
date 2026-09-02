# MEASURED-273: the closure-round fixes, and what re-measuring them found

Applies REVIEW-273-CLOSURE (`review/273-closure` @ `be2de5e`) to
`probe-273-packing.py` and to the probe's register entry in
`check-checkers-are-wired.py`. Every figure below was re-run on this
branch, not copied from the review.

## H1 - the false theorem is out of the docstring

The retracted claim ("when the largest item exceeds total/lanes ... greedy
is provably optimal") is replaced with the exhibited framing. Re-run
through the probe's OWN `lpt()` / `lower_bound()` / `best()`, with an
independent brute-force optimum over all `m**n` assignments:

    items=[27,23,22,16,13,9,8,6]  m=5  total/m=24.80  largest=27  dominates
      lower_bound=27.0  lpt=28.0  best=27.0  BRUTE-FORCE OPTIMUM=27.0
    items=[10,6,6,6]  m=3  total/m=9.33  largest=10  dominates
      lower_bound=10.0  lpt=12.0  best=12.0  BRUTE-FORCE OPTIMUM=12.0

Row 1 refutes "provably optimal" (LPT 28 vs optimum 27). Row 2 refutes the
max-bound half as well (optimum 12 > largest 10 under dominance). The same
retracted sentence was also in the register entry; it is gone from both.

## H2 - RESTARTS 60 -> 400, and lane 11 added

`RESTARTS` was the entire disagreement. One packer, two budgets:

| quantity | R=60 | R=400 | R=10000 | published as "round 6's" |
|---|---|---|---|---|
| 12-lane sharded best | 310.50 | **309.00** | 309.00 | 309.00 |
| re-anchored 12-lane win | 6.50 | **8.00** | 8.00 | 8.00 |
| U3 refit from 258s, 12 lanes | 305.60 | **304.00** | 304.00 | 304.00 |
| overhead-deleted, 12 lanes | 316.00 | 311.12 | **311.00** | 311.00 |

All four close. `§7a.2`'s "TWO PACKERS, AND MINE IS THE WEAKER ONE"
(`d314283:483-507`) describes a difference that does not exist.

The converged 12-lane cell is **309.0 sharded against an exact 311.0, a
-2.0s WIN**, which is what `§7a.2:465` publishes. The probe no longer
prints `-0.5s wash` against its own document.

Cost is not 8-10s: 400 restarts of `best()` on the 33-item instance takes
**11ms**, and the whole probe still runs in 1.3s wall, dominated by the
`gh api` call.

## The 11-lane row is a PROVED LOSS

Adding lane 11 - which the review prescribed so `§7a.2:480-481` could cite
the probe - prints a row nobody predicted:

       11 |   314.0  324.0  316.0~ |   333.1  347.0  335.5~ |  +19.5s loses

This is not a search artefact. The sharded LOWER bound (333.1) exceeds an
EXHIBITED unsharded packing (316.0), so sharding at 11 lanes loses by at
least 17.1s no matter how long either search runs. Sharding adds ~210s of
total work and below 12 lanes there is nowhere to absorb it.

`§7a.2:440-441` says "no reviewer has constructed a case where sharding
loses". On the printed table that sentence is now false. It needs scoping
to >= 12 lanes; it is not a threat to the 12-16 lane conclusion.

## M1 - '=' now means met, not "within half a second"

`abs(u_best - u_lb) < 0.5` -> `u_best <= u_lb + 1e-9`, both columns. The
review's two exhibited cases, re-run:

    lanes=3 LB 52.90 BEST 53.00 gap 0.10  OLD '='  NEW '~'
    lanes=3 LB 80.30 BEST 80.70 gap 0.40  OLD '='  NEW '~'

The genuine 12-16 lane cells still print `=` (gap exactly 0.0).

## M2 - SETUP is documented, not changed

13.0 stands, because every absolute published in `§7a.2` carries it. The
comment now records that this run's twelve lanes read 8-17s (median 11.5),
that 13.0 is the 9th of 12, and that it cancels in every delta. A footer
line says the same to whoever reads only the table.

## M3 - the register entry's magnitude

"a 2-4.6s WIN" -> "somewhere between a 2.0s win and a wash", matching
`d314283:536-539`. The reason it is unwired is unchanged and still true:
its inputs are one historical GitHub run.

## Verification

| check | before | after |
|---|---|---|
| probe | exit 0, 5 rows | exit 0, 6 rows |
| `EXPECT_STEPS = 34` | - | `REFUSING: population is 33, not 34.` exit 1 |
| `EXPECT_TOTAL = 3300` | - | `REFUSING: total is 3311s, not 3300s.` exit 1 |
| checker Members / WIRED / UNWIRED / unexplained | 149 / 75 / 74 / 0 | 149 / 75 / 74 / 0 |
| checker `--self-test` | 35/35 | 35/35 |
| `ruff check` + `format --check` | - | clean |

`WIRED` is unchanged, so no member moved WIRED -> EXEMPT. Member count is
unchanged because M3 edits an entry that already existed on this branch;
the review's 148 -> 149 is the branch-vs-`main` delta, not this change.

## Corrections to REVIEW-273-CLOSURE

1. Its Attack-2/3 finding that `§7a.2:440-441` "holds against every row in
   every table" no longer holds once its own H2/M4 fix is applied. The
   lane-11 row it asked for is a proved loss.
2. "400 restarts costs about 10s" - it costs 11ms.
3. Its unsettled item "R6's search is still marginally ahead" on the
   overhead-deleted refit is settled: 311.00 is reached at 10000 restarts
   (~0.3s). Budget, not search quality.
4. `§7a.2:545` "282.0 at 13 lanes" is confirmed as **283.00** (its L3).
