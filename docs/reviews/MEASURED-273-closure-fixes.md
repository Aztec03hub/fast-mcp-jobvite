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

## H2 - RESTARTS 60 -> 10000, and lane 11 added

`RESTARTS` was the entire disagreement. One packer, several budgets:

| quantity | R=60 | R=400 | R=10000 | R=40000 | published as "round 6's" |
|---|---|---|---|---|---|
| 12-lane sharded best | 310.50 | **309.00** | 309.00 | 309.00 | 309.00 |
| re-anchored 12-lane win | 6.50 | **8.00** | 8.00 | 8.00 | 8.00 |
| U3 refit from 258s, 12 lanes | 305.60 | 304.00 | 304.00 | **303.00** | 304.00 |
| overhead-deleted, 12 lanes | 316.00 | 311.12 | **311.00** | 311.00 | 311.00 |

All four close on round 6's figures, which is the point: the gap was the
budget. Two cautions on this table, both measured here and neither noted
when it was first written.

**Row 3's R=60 cell depends on which U3 shard value you feed it, not on
the search.** 138.6 - round 6's published figure - gives **305.60**;
138.62 - which `§7a.2`'s "The model INPUTS reproduced exactly" paragraph
says is what that section itself computes - gives **305.62**. Both
reproduce exactly at every budget, and the two are indistinguishable from
R=400 onward. `§7a.2`'s own budgets table prints 305.62 and this row
prints 305.60 because they feed different inputs, not because either was
carried forward unrun. Stated in both files so they cannot be read as
disagreeing.

**Row 3 is also not converged at R=10000.** It holds 304.00 from R=400
through R=10000 and then falls to **303.00** at R=40000, stable to
100000. Round 6's 304.00 was itself an unconverged reading. Rows 1, 2
and 4 are converged: 309.00, 8.00 and 311.00 are unchanged from R=10000
to R=100000.

`§7a.2`'s "TWO PACKERS, AND MINE IS THE WEAKER ONE"
(`d314283:483-507`) describes a difference that does not exist.

The converged 12-lane cell is **309.0 sharded against an exact 311.0, a
-2.0s WIN**, which is what `§7a.2:465` publishes. The probe no longer
prints `-0.5s wash` against its own document.

**Cost, measured rather than estimated.** Median of 5 trials on this
host, timing `best()` itself:

| what | R=60 | R=400 | R=10000 |
|---|---|---|---|
| `best(unsharded, 12)`, one cell | 3.3 ms | 22.4 ms | 552 ms |
| the whole 6-row, 2-column table | 53.7 ms | 355 ms | 8.81 s |

The earlier "8-10s" estimates were invented, and so was the **11ms** this
file published in their place: it matches neither quantity above at any
of the three budgets. One cell at R=400 is 22.4ms; the whole table is
355ms. At the `RESTARTS =
10000` the probe now ships, the table costs 8.81s and the wall is 13.5s,
so search - not the `gh api` call - now dominates. That is affordable on a
hand-run probe nothing gates, and it is the price of the 11-lane cell
being converged.

## The 11-lane row is a proved loss UNDER THE FITTED SHARD COSTS

Adding lane 11 - which the review prescribed so `§7a.2:480-481` could cite
the probe - prints a row nobody predicted:

       11 |   314.0  324.0  316.0~ |   333.1  347.0  334.0~ |  +18.0s loses

This is not a search artefact. The sharded LOWER bound (333.05) exceeds an
EXHIBITED unsharded packing (316.00), so under the fitted shard costs
sharding at 11 lanes loses by at least **17.05s** no matter how long
either search runs. Sharding adds ~210s of total work and below 12 lanes
there is nowhere to absorb it.

Two things this row is NOT.

**Not `+19.5s`.** That was the R=400 reading of `s_best`, a searched
upper bound; converged it is 334.0 and the delta is `+18.0s`. The
LB-vs-exhibited bound of 17.05s does not move with the budget - it is the
only budget-independent figure in the row.

**Not input-independent.** The whole bound is `sum(sharded)/11`, and
`sum(sharded) - sum(unsharded) = 209.6s` is FITTED overhead - the term
`#278` contests by a factor of 17-20. Measured across that range:

| shard model | sum(sharded) | s_LB(11) | vs exhibited unsharded 316.00 |
|---|---|---|---|
| as published (163.3 / 219.5) | 3520.6 | 333.05 | **+17.05s loses** |
| overhead-deleted refit (165.12 / 234.83) | 3554.9 | 336.17 | **+20.17s loses** |
| zero shard overhead (each step halved) | 3311.0 | 314.00 | **-2.00s, the bound REVERSES** |

At the zero-overhead end the loss is not merely unproved, it inverts: an
exhibited zero-overhead packing reaches **315.00** (R=10000, stable to
100000), a 1.0s win against the unsharded 316.00. `#278` measures the
overhead term at 130ms against the 2.24-2.64s fitted here, so the
reversing endpoint is the one the evidence points toward, not a
hypothetical. The row is budget-independent, not input-independent, and
the probe's footer now says so.

`d314283:§7a.2:440-441` said "no reviewer has constructed a case where
sharding loses". On the printed table that sentence was false and needed
scoping to >= 12 lanes; it was never a threat to the 12-16 lane
conclusion. `fix/7a2-two-packers` has since done the scoping, at
`§7a.2:440-441`, and retracts the general claim explicitly.

## M1 - '=' now means met, not "within half a second"

`abs(u_best - u_lb) < 0.5` -> `u_best <= u_lb + 1e-9`, both columns. The
review's two exhibited cases, re-run:

    lanes=3 LB 52.90 BEST 53.00 gap 0.10  OLD '='  NEW '~'
    lanes=3 LB 80.30 BEST 80.70 gap 0.40  OLD '='  NEW '~'

The genuine 12-16 lane **unsharded** cells still print `=` (gap exactly
0.0). Every **sharded** cell in that range prints `~`, before the change
and after - gaps 2.617 / 1.685 / 10.529 / 8.293 / 3.000 - so "both
columns" was never true of the `=` cells.

## M2 - SETUP is documented, not changed

13.0 stands, because every absolute published in `§7a.2` carries it. The
comment now records that this run's twelve lanes read 8-17s (median 11.5),
that 13.0 is the 9th of 12, and that it cancels in every delta. A footer
line says the same to whoever reads only the table.

## M3 - the register entry's magnitude

"a 2-4.6s WIN" -> "somewhere between a 2.0s win and a wash", matching
`d314283:536-539`. The reason it is unwired was unchanged by M3 and was,
at the time of this round, that its inputs were one historical GitHub
run. Both halves have since moved: the probe now fits three accepted
runs, and the 12-lane cell reads +5.0 / -1.0 / -4.0 and is NOT
determinate. The register entry in `check-checkers-are-wired.py` carries
the current wording; this section stays as the dated record of what M3
did.

## Verification

| check | before | after |
|---|---|---|
| probe | exit 0, 5 rows | exit 0, 6 rows |
| `EXPECT_STEPS = 34` | - | `REFUSING: population is 33, not 34.` exit 1 |
| `EXPECT_TOTAL = 3300` | - | `REFUSING: total is 3311s, not 3300s.` exit 1 |
| checker Members / WIRED / UNWIRED / unexplained | 149 / 75 / 74 / 0 | 149 / 75 / 74 / 0 |
| checker `--self-test` | 35/35 | 35/35 |
| `ruff check` + `format --check` | - | exit 0, exit 0 |

Re-verified in the closure round, at `RESTARTS = 10000`:

| check | result |
|---|---|
| both guard arms, one at a time | `REFUSING` before any table row, exit 1 each; file restored byte-identical (sha256 unchanged) |
| every printed cell, R = 1 ... 40000 | only `s11` moves past R=200; it settles at 334.0 from R=10000 to R=100000 |
| `:440`'s "12 lanes and above and nowhere else" | lanes 2-20 at R=2000, on the single-run fit this round measured: sharded wins at every lane >= 12, loses at every lane <= 11, no exceptions. On the tip's per-fit refit this no longer holds at 12 lanes, whose MIN fit is +5.0s, a loss. |
| `> 5s` strict filter | 32 steps / 3306s; the boundary is one `Install from the frozen lock` at exactly 5.0s |
| 12-16 unsharded gaps | 0.000 at all five, so `=` is correct |
| 12-16 sharded gaps | 2.617 / 1.685 / 10.529 / 8.293 / 3.000, so `~` is correct |
| the `a849f7f` run row | 35 steps / 3323s / largest 304s on run 33629034552 - the count and the largest hold, the total was this round's reading. The probe on the tip computes 3316s for that run, because its 35 counts the duplicated `Install from the frozen lock` in `WRAP` rather than in the population. Same count, different set, 7s apart. |

`WIRED` is unchanged, so no member moved WIRED -> EXEMPT. Member count is
unchanged because M3 edits an entry that already existed on this branch;
the review's 148 -> 149 is the branch-vs-`main` delta, not this change.

## Corrections to REVIEW-273-CLOSURE

1. Its Attack-2/3 finding that `§7a.2:440-441` "holds against every row in
   every table" no longer holds once its own H2/M4 fix is applied. The
   lane-11 row it asked for is a proved loss.
2. "400 restarts costs about 10s" - it costs 22.4ms for one cell and
   355ms for the whole table. An earlier version of this file replaced
   that with "11ms", which is no reading of any quantity; see the H2 cost
   table above.
3. Its unsettled item "R6's search is still marginally ahead" on the
   overhead-deleted refit is settled: 311.00 is reached at 10000 restarts,
   which costs 552ms for that cell. Budget, not search quality.
4. `§7a.2`'s "re-deriving U3's shard from the 258s it actually DREW"
   bullet (`d314283:545`) said "282.0 at 13 lanes"; it is **281.00**
   converged - 284.00 at R=60, 283.00 at R=400, 281.00 from R=10000
   through R=100000. An earlier version of this file reported it as
   "confirmed as 283.00", which was the unconverged R=400 reading, and
   that correction was never carried into `§7a.2` itself.
   `fix/7a2-two-packers` now fixes the line in place; this entry and that
   line were written in the same change so they cannot diverge again.
5. Its L3's sibling in that same bullet, "a 12-lane best of 304.0 - a
   7.0s win", is
   likewise unconverged: 303.00 at R=40000 and R=100000, an 8.0s win.
   Fixed on `fix/7a2-two-packers` in the same change.
