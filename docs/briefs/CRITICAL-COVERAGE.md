# CRITICAL-COVERAGE - two critical paths are under floor, and nothing enforces the floors

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `critical-coverage`. Your branch is `fix/critical-coverage`. Your report goes to
`docs/worklogs/CRITICAL-COVERAGE-REPORT.md`, committed on your branch. Your task record is **#94**.

## The measurement, taken at 708cbb2

`DESIGN.md:1364` names the critical paths: **auth, argument rejection, the error rule, approval, the
write.** ADR-0010 sets **95% line / 90% branch** on them.

```
module                  role                  line   branch  verdict
http_hardening.py       auth                 100.0%  100.0%  OK
utils/constraints.py    argument rejection   100.0%  100.0%  OK
errors.py               the error rule       100.0%  100.0%  OK
approval.py             approval              93.4%   78.6%  *** BELOW ***
tools/candidates.py     the write             92.1%   80.8%  *** BELOW ***
```

**Both misses are on BRANCH, by a wide margin** - 78.6% and 80.8% against 90 - not on line coverage,
which is the half people look at. Re-measure before you start; the tree has moved.

Uncovered at the time of measurement: `approval.py:282, 313, 338`; `tools/candidates.py:488,
558-562, 575, 684-687, 856->855, 858`. **Take those from your own run, not from this list.**

## THE TRAP, and it is the whole reason this brief is long

**Do not chase the number.** A test that executes a branch without asserting anything raises coverage
and proves nothing, and this project's entire record is that coverage of a branch is not evidence the
branch is checked:

- R3-M2 and R7-L1 were both assertions that could not fail.
- U1 had a surviving amputation under a green suite.
- R7's M4 added a payload-logging middleware to the production stack with all 663 tests passing.

**For every branch you cover, the test must be able to FAIL.** Amputate the behaviour it covers and
show the new test going red. A row you cannot kill is a row you have not tested - you have only
walked through it.

**If a branch is genuinely unreachable, that is a finding and a different fix.** Say so, prove it,
and mark it - `# pragma: no cover` with the reason, or delete the dead branch. An unreachable branch
dressed up with a test that reaches it artificially is worse than the gap, because it reads as
covered forever after.

## The second half, which is the durable one

`pyproject.toml:170-171` says:

> *"Only the overall floor is expressible as a single `fail_under`; the per-module floors are enforced
> by the units that create those modules."*

**That is a documented obligation enforced by nobody**, which is the shape this project has now
refused four times - a setting nothing reads (ADR-0025), a comment naming a variable that does not
exist, the `incomplete` flag (#86), and the row floors (#79). The aggregate gate is `fail_under = 80`
and the suite measures 95%+, so it stays green with two critical paths under their own floor.

**Build the checker.** Over `coverage json` output, and it must **read the critical-path list from
`DESIGN.md:1364` rather than carry its own copy** - a checker with a hand-kept list of the modules it
checks is the container defect this project has found seven times, and one of those was a checker I
wrote for exactly that defect.

Then wire it, **but only if it is green** - a gate that lands red is one people learn to ignore, which
this repository proved with a secret-scan step that was red for days and unread. If you cannot get
both modules to floor honestly, leave the checker unwired, say so, and file what remains.

## Also stale, while you are there

The same comment records *"measured at 92.66% over 552 statements"*. Current: 95.48% over 1588 - the
statement count has nearly TRIPLED. **Prefer prose with no number**, or derive it; a comment carrying
a measurement decays exactly this way, and this project has watched a retyped constant rot in a
brief, two obligation rows, a CI comment and three harness floors.

## Gates

Floors DERIVED from `ci.yml` by grep, never retyped - 810 and 421 as this was written, and they move
hourly. **0 skips.**

**Run the gate's OWN commands, argument for argument.** `uv run --frozen mypy`, NOT `mypy src` - I
reported "mypy clean" for a day from a command checking 23 files while CI checks 65, and shipped a
type error to `main` that way. `ci.yml:422` is the authority.

`ci.yml` is the orchestrator's; put the steps you need in your report.

## In the report

Per branch covered: what it does, the test, and the amputation that proves the test can fail. Any
branch you judged unreachable, with the proof. The checker, and whether you wired it. Then what you
could not settle.
