# HARNESS-GATES - the gates around the harnesses are the least-tested thing here

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `harness-gates`. Your branch is `fix/harness-gates`. Your report goes to
`docs/worklogs/HARNESS-GATES-REPORT.md`, committed on your branch.

**You own tasks #27 and #29. Do #27 first** - a shared gate script is the natural place for #29's
uniform check, and doing them separately means writing the same shell twice.

## Why this exists

`B49b` reflowed 1608 lines. One of them was inside a mutation anchor in `check-u3-audit-controls.sh`,
so row M8 matched nothing, and **a mutation that applies to nothing tests nothing.** CI caught it
only because that one step happened to grep for `COULD NOT APPLY`.

So the thing guarding the harnesses is itself the least-instrumented code in the repository.

## Task #27 - the step body is not runnable

The U1 amputation gate's logic lives inline in a `ci.yml` `run:` block: three exit-code branches, the
anchor greps, the `rows -ge 14` count. It cannot be run locally, reviewed as code, or exercised by a
control.

The previous agent verified its change by hand-copying that block into a local script and replaying
recorded harness output - and then **deliberately did not commit the copy**, because a hand-copied
twin of a gate is the two-lists defect: `ci.yml` moves, the copy does not, and the copy keeps
passing. That refusal was correct and it is why this task exists.

**Extract the step body to a script `ci.yml` calls**, list it in `CONTRIBUTING.md`, and write a
control for it - feed it a recorded harness log carrying an `UNEXPECTED SURVIVOR` and require exit 1.
Recorded logs are the right fixture here; do not synthesise one if a real one can be captured.

**SCOPE DECISION, YOURS TO MAKE AND TO STATE.** Every other step in `ci.yml` is inline, so doing this
to one step makes the file inconsistent. Either accept that and say why in a comment, or convert the
sibling harness steps in the same pass. Both are defensible; an unstated choice is not.

## Task #29 - six of eleven steps cannot detect a stale anchor

Measured from `ci.yml`:

```
OK   U1 boot amputation, U3 mutation, U3 amputation, U4 mutation, U4 amputation
GAP  U0 test controls, U15 gate controls, U15 gate amputation,
     U11 advisory controls, U1 boot mutation controls, suite-floor amputation
```

**DO NOT FIX THIS BY COPYING ONE GREP INTO SIX STEPS.** The harnesses use different vocabulary,
measured:

```
check-u0-test-controls.sh        DID NOT FIRE, STAGING CONTROL
check-u15-gate-controls.sh       DID NOT FIRE
check-u11-advisory-controls.sh   DID NOT FIRE
check-u1-boot-controls.sh        DID NOT LAND
check-suite-floor-amputation.sh  ANCHOR MISSING, ANCHOR NOT UNIQUE, DID NOT LAND
check-u15-gate-amputation.sh     NOTHING AT ALL
```

**A grep for a string a harness never prints is an inoperative gate** - the same defect as the stale
anchor, from the other side. Six new inoperative greps would be worse than the present gap, because
they would look like coverage.

**The sharpest item: `check-u15-gate-amputation.sh` has no anchor-failure vocabulary whatsoever.** It
cannot report that a mutation failed to apply, so no step can gate on it. Check whether it asserts
its anchors at all; it needs the capability before it can have a gate.

Suggested order: give every harness ONE shared phrase for "my mutation did not apply" - pick from
what exists rather than inventing a seventh; `DID NOT LAND` is used by two and is the most accurate -
then gate uniformly.

## The idea worth more than either task

**A static checker that reads each harness's anchors and greps its target file for them**, so a stale
anchor is caught without running the harness. A run is minutes; this is milliseconds. A B49b-style
sweep is exactly when you want it cheap, and it would have caught M8 the moment the sweep landed.

Treat this as the deliverable if the extraction proves larger than it looks. **Measure how many
anchors are currently stale across all thirteen harnesses before you build it** - if the answer is
zero, say so; that is still the measurement, and it establishes a baseline the checker defends.

## Two things that will bite

- **A harness mutates `src/` in place.** Never run a gate pass while one is running, and never
  `git add -A` during one - two commits captured an amputated tree that way. Verify the tree is clean
  with `git status` after every harness run.
- **`git diff` is blind to an UNTRACKED file** - it reports no difference whatever the file contains.
  Use `cmp` against a backup. Four rows once reported "did not land" when all four had landed.

## In the report

The stale-anchor count across all thirteen harnesses. Your scope decision on #27 and why. What each
gap step now gates on, and the vocabulary you unified to. The control you wrote for the extracted
gate, and proof it goes red. **End with what you could not settle.**
