# REPORT — #147: the CI-step probe's selection bias

`suborch-147`, 2026-09-01. Branch `fix/147-ci-step-selection`, commits
`6d2fca1` and `a865573`, cut from `main` at `203e5af`. Not pushed, not
merged.

**Every number below is measured at `203e5af` in my own worktree.** The
workflow is being edited by `suborch-143` right now, so a count taken
after that lands will differ and this file states its SHA for that
reason.

---

## 1. Corrections to my brief

Every one of these is a number the brief handed me as fact, re-measured.

| The brief said | Measured at `203e5af` |
|---|---|
| runs **12** of 78 | runs **13** of 78 — 12 classified + the actionlint line lifted |
| skips **36** as multi-line | skips **34**, plus the 1 lifted = **35** blocks |
| **29** not a checker invocation | **30** |

The brief's 36/12/29 were true when #147 was filed and had already moved
by dispatch. **The 78 is right and is the one number that needs its
container spelled out**: 78 `run:` steps **in `ci.yml` alone**. All
workflows together is **80** (`ci.yml` 78, `mirror.yml` 2, `pr-title.yml`
0), and §D warned that those two have been confused here before. They are
still confusable; this report and the probe both say `in ci.yml ONLY`.

**A fourth correction, to §C's framing rather than its numbers.** The
brief says a step is multi-line "precisely because it carries a flag, an
env var, or `|| exit 1` handling". That is true of most of the bucket and
FALSE of fourteen of them: steps 16-28 and the licence gate are ONE
command split across two physical lines with a backslash. `classify()`
counted physical lines, so a line continuation read as "a block with its
own setup". Those fourteen were filed under a reason that was not true of
them — and a wrong reason in a skip table is worse than a skip, because it
tells the reader the step is structurally unrunnable when the real cause
was newline counting.

---

## 2. What the numbers are now

```
                          before (203e5af)   after
steps RUN (exit-equivalent)      12            13
lines LIFTED (step NOT covered)   1             7
invocations executed             13            20
multi-line block, own setup      34             0
```

Balance holds: `13 run + 7 lifted + 58 skipped = 78`, and the probe still
refuses to print any number if that identity fails.

**The bucket was emptied by reading the blocks, not by loosening
`_SHELLY`.** `_SHELLY` is unchanged, and every extracted command is still
put through it before it runs. Three shapes are recognised:

1. **a backslash continuation is joined** — it was never a block;
2. **`set …` + one invocation + `|| { echo …; exit 1; }` is RUN**, because
   a guard that only prints and exits nonzero cannot move the exit code
   the invocation produced. `_guard_is_inert()` checks each statement in
   the brace group and returns False for anything that is not
   `echo`/`printf`/`exit N`, so a retry or a rescuing `exit 0` is refused
   rather than assumed away;
3. **`out=$(cmd 2>&1); rc=$?` + assertions is LIFTED** — the invocation
   runs, the STEP IS NOT COVERED, and the two go in different buckets.
   That is R14's H-1 rule applied to six more steps.

### What remains unrunnable, with its reason

| n | reason | is it honest? |
|---|---|---|
| 52 | no `check-*.py` invocation in the step | **partly — see §5** |
| 7 | one line LIFTED, step not covered | yes, by construction |
| 4 | MUTATES THE TREE or costs minutes | yes, verified |
| 2 | a NONZERO exit is tolerated by the step | yes, verified |

- **The 4.** `check-coupling-controls.py`, `check-coupling-sweep.py`,
  `check-obligations.py --controls` all EDIT the document they gate (their
  own CI steps grep for `post-run re-check of the real DESIGN.md: exit=0`),
  and `check-coverage-floors.py` costs minutes. **`_DESTRUCTIVE` had to
  GROW for this change**: it covered `-controls.sh` only, which was
  sufficient while the reachable set was twelve single-line steps and
  became insufficient the moment blocks were opened. A deny-list that is
  correct for the population it was written against is the same shape as
  the defect this task is about, and it is worth saying that this one was
  caught by looking rather than by a gate.
- **The 2.** `check-clause-citations.py` and `check-standards-citations.py`
  exit 2 when the private standards sibling is absent — the normal local
  state, and the runner's (#106). Their steps `exit 0` on rc==2 on
  purpose. Lifting the invocation would give a probe RED where CI is
  GREEN: a false red manufactured out of a configuration difference, which
  is the first of the two failures this probe was written for. So they
  stay counted, and the reason names the mechanism rather than saying
  "hard".

---

## 3. The argument arm, and the second instance nobody had looked for

**Container, enumerated not listed:** every `check-*.py` invocation line
in `ci.yml`. **25 lines**, all 25 reachable, **4 carry arguments**, 1 of
those refused as tree-mutating, **3 run both ways**.

| invocation | bare vs CI's form | verdict |
|---|---|---|
| `check-committed-file-types.py --all` | 437 files vs **0 files** | the known instance |
| `check-harness-anchors.py --self-check --floor 458` | floor 458 vs **floor 0** | **NEW** |
| `check-coupling.py docs/DESIGN.md` | same file, absolute path printed | cosmetic |
| `check-obligations.py --controls` | not run (mutates) | — and CI runs BOTH forms anyway, which is the pattern the other three lack |

### The new one

`scripts/check-harness-anchors.py`'s `--floor` **defaults to 0**
(`ap.add_argument("--floor", type=int, default=0, …)`). Measured: the bare
form prints `anchors resolved: 458` / `OK` and exits 0; `--floor 999`
exits 1. So if a parser shape stopped matching and the resolved count fell
from 458 to 10, the bare form prints *"all 10 anchors resolve. OK"*, exits
0, and every row those 448 anchors covered is unchecked. The bare form
also skips `--self-check`, the harness's own positive control.

**The flag's own help text is the description of this failure:** *"the
count drops and every row it covered goes unchecked WITH THE RUN STILL
GREEN"*. The checker documents the defect that its own bare invocation
has.

**And `CONTRIBUTING.md` prescribes the weaker form.** Its local block is
`python3 scripts/check-harness-anchors.py --self-check` with no `--floor`,
and the comment says why: *"The floor is in ci.yml, the one place it
lives."* That reasoning is right — a retyped floor is a two-lists defect —
and its consequence was simply unwatched. **The arm added here is the
resolution of that tension: it DERIVES the flag from `ci.yml` and runs
both forms, so nothing is retyped and nothing is unwatched.** I did not
edit `CONTRIBUTING.md`; it is outside §B and the change I would suggest is
one line under "the gates" pointing at the probe.

### What the arm fails on, and what it only reports

- **Different exit codes FAIL the probe.** One form is green and the other
  red on this tree right now, so somebody running the bare form locally is
  being told something CI does not agree with.
- **Same exit, different output is REPORTED.** That is exactly the state
  `--all` was in for each of the 127 commits before the tree broke. It is
  worth printing and it is not by itself a defect — making it fail would
  be red on a healthy tree from the day it landed, which is how a gate
  gets switched off.

---

## 4. Controls: 8/8, and BOTH of my first two versions were vacuous

`docs/reviews/probe-ci-checker-steps-control.py`, exit 0.

```
A   clean, swap ACTIVE                       green, no traceback
C1  ci.yml mutated, swap ACTIVE              red on its OWN traceback
C2  ci.yml mutated, swap AMPUTATED           red, borrowed, no traceback
E1  whole-tree step BROKEN, blocks ACTIVE    red    <- the fix works
E2  whole-tree step BROKEN, blocks AMPUTATED GREEN  <- the bias itself
D   restored, swap ACTIVE                    green
F1  tree perturbed, arm ACTIVE, blocks OFF   red, and it SAYS "DISAGREE"
F2  tree perturbed, arm OFF, blocks OFF      GREEN  <- the blindness
```

**E2 is the measurement, not E1.** A green over a demonstrably broken CI
step, produced by putting the old classifier back, is the selection bias
observed rather than argued.

**Both first versions of these arms were passing for another mechanism's
reason — the exact failure this control file was created to fix, rebuilt
twice more:**

- **E, first version:** the argument arm was left running. The mutation
  (`--all --amputated`) still carries an argument, so the arm caught the
  disagreement on its own and **E2 came back RED**. E1's red was borrowed.
  Fixed by amputating the argument arm in both E arms.
- **F, first version:** the block reader was left running. The probe now
  RUNS the whole-tree step, so it goes red on the perturbed tree with the
  arm switched off, and **F2 came back RED**. Fixed by amputating blocks
  in both F arms — which is also the right question, since before this
  branch no probe ran that step at all, so F1/F2 are literally the world
  in which the 127-commit red happened.

The control caught both. Neither would have been visible from the exit
code alone; both were found by reading WHICH arm died.

**F's perturbation** appends a NUL byte to a tracked file the control
OWNS (itself). `--all` reads WORKTREE blobs of TRACKED paths, the bare
form reads the STAGED set, so an unstaged NUL is refused by CI's form and
invisible to the bare one — the 127-commit shape with no commit and no
other agent's file touched. **It is guarded on BYTES, not `git status`**:
the prior bytes are held and written back, so restoration is provable
directly and more strongly than git can. The git guard is right for
`ci.yml`, which the control does not own; here it made the control refuse
to run on any tree where the file was being edited, which is every tree
where it is being worked on. Measured — the first version refused itself.

---

## 5. What I did NOT settle, and what I am handing over

**These are open, not untried.**

1. **`_CHECKER` is `.py`-only, so the 52-bucket is honest about the probe
   and misleading about the workflow.** Thirteen of those 52 steps run
   `check-*.sh` harnesses through `scripts/ci-harness-gate.sh`; they ARE
   gates. I renamed the reason to `no check-*.py invocation in the step
   (this probe's selector)` so it states the selector rather than implying
   the step is not a gate, and I did NOT widen `_CHECKER`. Widening it
   pulls every mutation harness into reach at once, and the deny-list has
   already had to grow once in this change. **This is #153's family: a
   selector that picks by path or extension is blind to the member outside
   it.** It wants its own task, with the deny-list re-derived first.
2. **The `check-*.sh` gates carry arguments too** and are outside the
   argument arm's container for the same reason. `check-pytest-bounded.sh`
   is run twice in one step, `--self-test` then bare — CI asks both
   questions there, which is the correct pattern and worth copying.
3. **The cosmetic `DIFFERENT` on `check-coupling.py` is noise** and will
   train a reader to skim the arm's output. I left it: suppressing it
   needs a rule for "the difference is only a path", and a rule like that
   is how a real difference gets suppressed later. Printing the differing
   line makes it self-evident instead.
4. **I did not measure whether any checker's bare form is weaker in a way
   that produces IDENTICAL output.** The arm cannot see that, and I have
   no evidence such a case exists here.

**On #153** (asked for in §E): the wiring checker selects by path; this
probe selects by path AND extension AND, until this change, by newline
count. Three selectors, three different blind spots, one workflow. Nothing
enumerates the container of "things `ci.yml` runs as a gate" and compares
it against any of them.

---

## 6. Gates

All run from the worktree with CI's exact invocation.

```
uv run --frozen ruff check .          exit 0   All checks passed!
uv run --frozen ruff format --check . exit 0   128 files already formatted
uv run --frozen mypy                  exit 0   no issues in 128 source files
uv run --frozen pytest                exit 0   887 passed, 6 deselected, 0 skipped
uv run --frozen python docs/reviews/probe-ci-checker-steps.py           exit 0
uv run --frozen python docs/reviews/probe-ci-checker-steps-control.py   exit 0  (8/8)
```

887 passing matches `ci.yml`'s suite floor of 887, and the zero-skips
guard is satisfied. The probe's whole run is 5.7s wall. I did NOT measure the
before-figure, so I am not claiming a delta: what I can say is that it
now executes 20 invocations instead of 13, and that the slowest new one,
`check-plan-measurements.py`, is 6.3s measured alone — which is longer
than the whole probe takes, so the invocations are evidently not the
serial cost they look like.

**Not run, and why:** `check-clause-citations.py` and
`check-standards-citations.py` beyond the probe's own handling — they need
the standards sibling; `bash scripts/check-u1-pid1-shutdown.sh` — needs
Docker; the thirteen `ci-harness-gate.sh` harnesses — minutes each and they
mutate the tree, and `suborch-143` is live in this repo.

**I did not push and did not merge.** `.github/workflows/ci.yml` is
byte-identical to `203e5af` on this branch; the control restores it and
`git status --porcelain -- .github/workflows/ci.yml` is empty.
