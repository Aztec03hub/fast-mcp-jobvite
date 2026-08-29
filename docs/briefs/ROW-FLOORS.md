# ROW-FLOORS - ten harnesses report green with all but one row deleted

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `row-floors`. Your branch is `chore/row-floors`. Your report goes to
`docs/worklogs/ROW-FLOORS-REPORT.md`, committed on your branch. Your task record is **#79**.

## The defect, already measured - do not re-litigate it, extend it

`FIRED -ne TOTAL` is satisfied by `0 == 0`. A harness whose rows were deleted reports fully green.

Measured on `check-u9-http-controls.sh` at `b8bad8d`, both arms, one row kept and thirteen deleted:

```
without the floor (the code as it stood)   1/1 controls fired    exit 0
with the floor                             1/14 ROWS             exit 1
```

`TOTAL -gt 0` is not useless - deleting ALL rows gives `0/0` and exit 1. What it cannot see is
**partial** deletion, which is the realistic shape: a refactor that drops rows, or an anchor that
stops matching so a row silently stops being counted.

## Your population, and where it came from

Run `python3 docs/reviews/check-row-floors.py`. It joins the harness directory against `ci.yml` and
reports every harness with no floor at **either** layer - no internal `ROW_FLOOR=<n>`, and no
`--min-rows <n>` from `ci.yml`. Ten, as of `40ce300`:

```
check-harness-anchors-controls.sh   check-suite-floor-amputation.sh
check-u0-test-controls.sh           check-u1-boot-controls.sh
check-u11-advisory-controls.sh      check-u15-gate-amputation.sh
check-u15-gate-controls.sh          check-u3-audit-controls.sh
check-u4-client-controls.sh         check-u7-resilience-controls.sh
```

**Take the list from the checker, not from this brief.** This one was measured at a commit that is
already behind you, and a count copied into prose is the defect the checker exists to catch.

## THE ONE RULE THAT MATTERS: DERIVE EVERY FLOOR

**Run the harness. Read its own row count out of its own output. Use that number.**

Do not copy a count from a task record, a worklog, a report, or this brief - several of them contain
the right numbers and that is exactly the trap. Branch-local floors have been wrong on this project
four times, and a value measured once should appear once. A typed floor clears the checker and buys
nothing; a WRONG typed floor is worse than none, because it looks like the work was done.

If a harness will not run, say so and leave it floorless. **A harness you could not run is not a
harness you may guess a floor for.**

## A harness owns the working tree for its whole run

Measured four times in one day by two agents. So:

- **One harness at a time.** Do not background two.
- **Never wrap one in a `timeout` short enough to fire** - killing it mid-row leaves its mutation in
  the tree, and the full suite has passed with such a mutation in place.
- **Do not read the tree, run the suite, or commit while one is running.** Anything measured in that
  window measures the harness.
- These run the suite once per row. Budget roughly 15-25 minutes each. Ten of them is most of a day
  and that is expected - say so in your report rather than rushing.
- Before each run, confirm the tree is clean. A harness that refuses to start on a dirty tree is
  protecting you; an exit 3 from a precondition check is not a defect to route around.

## Two traps that have already caught someone here

**The tally line's prefix.** R7 found that `check-u9-http-controls.sh`'s tally line has no
`##########` prefix, so wiring it with `--row-re '^########## M[0-9]+ '` would match **zero** rows
and fail the step for the wrong reason. **Prefer the internal `ROW_FLOOR`** - copy the shape from
`check-u8-candidates-controls.sh:480-493`. If you do add a `--min-rows` to `ci.yml`, you MUST check
its `--row-re` against the harness's real output and report the count it matches.

**A row a static checker cannot read.** U14 hit a row that bash executed correctly and reported
KILLED, while `check-harness-anchors.py` found 0 hits for its anchor - nested quotes and
backslashes. A row the harness runs and the checker cannot see is a row nobody is checking. Run
`python3 scripts/check-harness-anchors.py --self-check --floor 401` after every change.

## `ci.yml` is MINE. Do not edit it.

If a harness needs a `ci.yml` change, put the exact lines in your report and I will apply them.

## Wiring the checker

Once every harness in the checker's output has a floor, **wire `check-row-floors.py` into `ci.yml`**
- by giving me the step, not by editing the file. If any harness could not be run, it stays
floorless and the checker stays unwired: a gate that lands red has been refused three times here.

## Gates

Derive the suite and anchor floors from `ci.yml` by grep; never retype them. **0 skips** - compare
PASSED counts. Run the full gate before folding, not after. Your change should not move the suite
count at all: you are editing harnesses, not tests. If the count moves, something is wrong and that
is a finding.

## In the report

A table: harness, rows measured, floor set, and **the line of its output you read the count from**.
Then the wiring steps for me. Then what you could not settle - and that list is for what you CANNOT
settle, not what you did not try.
