# MEASURED: the CI re-tier

**Branch `ci/294-retier`, based on `3c0d648`. Referent: `docs/reviews/MEASURED-baseline-pre-retier.md`,
tag `baseline/pre-retier` at `305fd05`, run `33680282835`.** Written 2026-09-02.

Every figure below is either read out of that baseline, or measured on this machine and labelled
LOCAL. Nothing here has run on a GitHub runner: this branch was deliberately not pushed, so the
CI-side numbers are the baseline's own per-job figures re-arranged, and they are marked as such.
That distinction is the whole reason the wall-clock claims below are stated as *unchanged content
in a different job*, and never as a new measurement.

---

## 1. THE `cancel-in-progress` FINDING, WHICH WAS THE HIGHEST-VALUE ITEM IN THE PLAN

**It is already there, and it is deliberately CONDITIONAL.** At `.github/workflows/ci.yml:88-89`,
unchanged by this branch:

    concurrency:
      group: ci-${{ github.event_name }}-${{ github.ref }}
      cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

So: **on** for every branch and every pull request, **off** for `main`. Both halves are argued in
the fifty lines of comment above them, and the argument is a measurement rather than a preference:
on 2026-08-29 `main` had 54 cancelled runs, 5 failures and ZERO successes in one day, and because a
`cancelled` conclusion is not a failure, nothing anywhere read as red while the trunk had been
broken for hours. Every push simply cancelled the evidence that the previous one was broken.

The event name is in the group key so a scheduled sweep and a push to `main` cannot cancel each
other. That is also unchanged.

**Nothing to do.** The plan's 2.5 is already satisfied and was satisfied more carefully than the
plan asked for: a blanket `cancel-in-progress: true` would re-create the 54-cancellations state on
the trunk. The item that "one repo elsewhere in the org consumed 83% of the August bill" for is
closed here, and the residual - GitHub keeps at most ONE PENDING run per group, so a commit can
still land with no run of its own - is already recorded in the same comment.

---

## 2. WHAT MOVED WHERE

Sixteen jobs became five. No check was deleted; the invocations are byte-identical, flags included.

| before (16 jobs) | after | tier |
|---|---|---|
| `test` "Lint, types, tests" | `test` "Gate - lint, types, tests", unchanged content | **Gate** - every push, every PR |
| `static-gates` | same job, `if: github.event_name != 'pull_request'` | **Merge** |
| `codeql` | same job, same `if:` | **Merge** |
| - | `changes`, new, 1 step | **Merge** |
| 12 `harness-*` lanes (35 steps) | folded into `harness-assurance`, serial | **Assurance** |
| `wiring-probe` (2 steps) | folded into `harness-assurance`, LAST | **Assurance** |

Triggers:

| tier | fires on |
|---|---|
| Gate | every push to `main`, every pull request. No `if:`, by design |
| Merge | `github.event_name != 'pull_request'`: push to `main`, weekly cron, manual dispatch |
| Assurance | weekly cron, `workflow_dispatch`, and a push to `main` that `changes` classifies as code |

### Why one file and not three workflows

Three workflow files would express the triggers natively - `on: push: paths:` exists and a
job-level `if:` cannot see paths at all. It was refused because three live checkers join on this
path and would have gone quietly wrong:

1. `docs/reviews/check-row-floors.py:48` and `check-row-floor-exactness.py:190` read `--min-rows`
   out of `.github/workflows/ci.yml` **by path**. Harness steps in a second file are floors those
   two cannot see - and a floor nothing reads has been retuned to zero without anyone typing a
   digit. Constraint 6 of the brief forbids exactly that, and a file split would have done it
   silently.
2. `scripts/check-mirror-liveness.py:111` watches EVERY scheduled workflow in `.github/workflows`
   and reports NEVER RUN, exit 2, for one with no runs. A second `schedule:` therefore turns the
   trunk red until the day it first fires - a red for something no commit contains.
3. `docs/reviews/probe-ci-checker-steps.py:179` and `probe-control-restore-guard.py:37` both pin
   this path.

The price of that choice is the `changes` job: one extra billed minute per push to `main`, buying
the discrimination `on: paths:` would have given free.

---

## 3. THE PATH FILTER, BY ROLE, WITH BOTH ARMS MEASURED

Constraint 5 asks for discrimination by ROLE and not by directory, and `docs/reviews/` is why:
`*.py` and `*.sh` there are checkers and probes, `*.md` beside them are records. The `changes` job
classifies with one ERE, and it was driven in both directions on a synthetic repository (LOCAL):

    README.md                          code=false
    docs/adr/0001-x.md                 code=false
    docs/reviews/REVIEW-R1.md          code=false     <- a RECORD
    docs/reviews/check-thing.py        code=true      <- a CHECKER, same directory
    docs/reviews/probe-x.sh            code=true
    scripts/check-u1.sh                code=true
    src/a.py                           code=true
    BEFORE = 0000...0000               code=true      <- fail-closed

The fail-closed arm is not decoration. A force-push, a first push, or a missing object all make the
diff unreadable, and the expensive direction is the safe one.

### What is NOT filtered, and why the brief's "a README-only change must not run the suite" is refused

Markdown here is not inert, and this was measured rather than assumed, on a clean worktree at
`3c0d648`, in both directions:

- **Positive arm.** Deleting `JOBVITE_COMPANY_ID` from README.md's Quickstart block - a
  README-only edit, no code touched - takes `The README's Quickstart still works` from exit 0 to
  exit 1. That step EXECUTES the README.
- **Negative arm, and it is the reason this paragraph is careful.** APPENDING a second fenced block
  to the same file changed nothing: rc=0 both times, because the checker reads the Quickstart block
  and not the prose.

So the defensible claim is narrow - SOME markdown edits redden a wired gate, and a blanket `.md`
filter cannot tell which - and the Quickstart is not the only route: `check-brief-report-references.py`
rglobs every `.md` under the briefs tree, the lychee step walks the whole checkout, and the design-
and standards-citation gates read `.md` prose for line-anchored citations.

A workflow-level `paths-ignore: '**/*.md'` would therefore switch those gates off on exactly the
changes they exist to catch, and a switched-off gate and a working one render identically - the
failure mode that hid 119 red mirror runs on this repository. It would have saved the suite's share
of one job. **Refused, and recorded here rather than left unexplained.**

---

## 4. WALL CLOCK

### Gate tier

**LOCAL, all 31 run steps of the `test` job, executed under GitHub's own
`bash --noprofile --norc -eo pipefail`, 31 of 31 exit 0: 83.6s of step time.**

    7.4s  Types (mypy)
   57.2s  Default suite, zero skips
    4.8s  Commit-time hooks - secret scan, shellcheck, file types
    3.7s  Dependency audit
    2.3s  Docs-lint amputations
   <2s    every one of the other 27 steps

**On a GitHub runner this job measured 220s at the baseline, and this branch does not change one
byte of its content, so 220s is still the number to expect. THE UNDER-3-MINUTE TARGET IS MISSED BY
THE BASELINE'S OWN FIGURE, at 3.67 minutes.** It is stated that way rather than as a target because
nothing here was retuned to reach it: the brief's own reading - that `Lint, types, tests` "is,
almost exactly, the Gate tier" - is correct, and that job was already 220s.

Getting under 180s would mean moving the suite (125s of the 220s) off the push path, which is the
one thing the Gate exists to run. **Not attempted. The measured number is 220s.**

### Merge tier

**LOCAL, all 25 run steps of `static-gates` executed against THIS branch's `ci.yml`, 25 of 25 exit
0: 9.8s of step time.** Baseline job wall 55s. CodeQL 76s at baseline, unchanged. `changes` is one
`git diff` plus one `grep` over a `fetch-depth: 0` checkout.

### Assurance tier

**LOCAL, all 38 run steps of `harness-assurance` executed end to end in one tree, in file order,
each under `bash --noprofile --norc -eo pipefail`: 1063s = 17.7 minutes, 38 of 38 exit 0.** Every
harness printed its own full tally; no step was skipped and none was vacuous.

The eight heaviest, LOCAL:

    111.8s  U9 HTTP hardening amputation, every row applied
    104.5s  U3 audit amputation harness ran every row
    100.5s  U1 boot mutation controls, all fired
     89.2s  U1 boot amputation harness ran every row
     71.9s  U4 client amputation harness ran every row
     65.3s  Critical-path coverage amputation, every row applied
     60.1s  U7 resilience amputation, every row applied
     57.7s  U0 test controls, all fired

**That 17.7 min is this machine, not a runner, and the two must not be compared.** The CI-side
figure is derived from the baseline's own per-job walls instead, and the derivation is written out
so it can be checked rather than trusted:

    the twelve harness lane walls, from the baseline table
      337 330 293 274 254 250 229 220 218 180 160 158      sum 2903s
    minus twelve lane setups at probe-273-packing.py's measured SETUP = 13.0s
                                                            -156s
    harness work                                            2747s
    plus ONE setup for the merged job                        +13s
    plus the wiring probe's work (its 20s job less its setup) +7s
    ------------------------------------------------------------
    serial job wall                                         2767s = 46.1 min

**46.1 minutes, which is BELOW the 60-70 minute target band rather than inside it.** Two things
about that number: the setup term is the probe's own constant, whose 36 accepted lanes read 8-19s
with a median of 11.0, so the 156s subtraction carries roughly +-70s of uncertainty; and it assumes
serialising changes no step's duration, which is true for CPU-bound work on a dedicated runner and
is the same assumption the twelve-lane arithmetic already makes in the other direction.

### One step failed on the first pass, and it was my fault, not the harness's

`U6 paging controls, all fired` exited 1 during the batch. The harness itself passed -
`rows=16 floor=16 fired=16/16 status=ok` - and it was `scripts/ci-harness-gate.sh` that failed
after it, with `DID NOT RESTORE THE WORKING TREE` and this as the whole of its evidence:

    ?? docs/reviews/MEASURED-294-retier.md

That is THIS FILE. I wrote it into the worktree while the batch was running, and the gate's restore
check compares the whole tree before and after, so an unrelated untracked file created by someone
else during the run reads as a stranded mutation. Re-run alone on a quiet tree: **rc=0, 16/16,
`status=ok`, 7s.**

**This is a real property of `ci-harness-gate.sh` worth writing down, and it is not a defect to
fix.** In CI it cannot fire - nobody else writes to the runner's checkout - and erring towards
refusal is the correct direction for a check whose job is to catch a mutation left in source. In a
developer or agent worktree it produces exactly this false red, and the diagnosis is in the message
if you read the path it prints rather than the headline.

It also happens to be a two-instrument disagreement worth naming: the new
`The serial lane left no mutation in src or tests` step passed on that same batch, because it scopes
to `src` and `tests`. The two checks are asking different questions, the narrower one is mine, and
neither replaces the other.

---

## 5. BILLED MINUTES

GitHub rounds **every job** up to a whole minute, so the bill is a sum of ceilings and not a ceiling
of the sum. The repository is PUBLIC and bills nothing today; these are the counterfactual for the
private child repositories the template will seed, which is the reason the re-tier optimises this
column and lets wall clock follow.

### Before, from the baseline's own per-job table

    16 jobs, EVERY trigger:  61 billed minutes
    of which                  6.4 min is pure per-job rounding - 10%, from having 16 lanes

### After

| event | jobs that run | billed |
|---|---|---|
| pull request push | `test` | **4** |
| push to `main`, records only | `test` + `static-gates` + `codeql` + `changes` | **8** |
| push to `main`, code | the four above + `harness-assurance` | see §4 |
| weekly cron | `test` + `static-gates` + `codeql` + `harness-assurance` | see §4 |

**The headline: a pull-request push goes from 61 billed minutes to 4, a 93% reduction, and that is
the event that happens most.** A records-only push to `main` goes 61 to 8.

### The full table, ceilings taken per job

The 61 is reproduced from the baseline's own per-job walls before anything is claimed about the
after, because a before nobody re-derived is a number, not a referent:

    twelve harness lanes  6+6+5+5+5+5+4+4+4+3+3+3 = 53
    Lint, types, tests                          220s ->  4
    CodeQL                                       76s ->  2
    Static gates                                 55s ->  1
    wiring-probe                                 20s ->  1
    ----------------------------------------------------
                                                        61   <- matches the baseline exactly

After, with `harness-assurance` at ceil(2767/60) = 47:

| event | jobs | billed | vs 61 |
|---|---|---|---|
| pull-request push | test 4 | **4** | **-93%** |
| push to `main`, records only | 4 + 1 + 2 + 1 | **8** | -87% |
| weekly cron | 4 + 1 + 2 + 47 | **54** | -11% |
| push to `main`, code changed | 4 + 1 + 2 + 1 + 47 | **55** | -10% |

### THE ONE NUMBER THAT NEEDS A DECISION, AND IT IS NOT MINE TO MAKE ALONE

**The `push to main, code changed` trigger costs 47 of its 55 billed minutes, and it is the row
that eats almost the whole saving.** The plan asks for it in as many words - Assurance fires on
"weekly cron + workflow_dispatch + on harness/src change" - and it is built and works, so this is a
measurement rather than an objection.

The trade, stated plainly so it can be overruled with the number in hand:

- **Keeping it**, a merge to `main` that touches code costs 55 billed minutes instead of 61. Every
  code change is fully harness-verified before it has been on the trunk for a day.
- **Dropping it** - deleting the single clause
  `|| (github.event_name == 'push' && needs.changes.outputs.code != 'false')` - takes that same
  merge to **8**, an 87% cut, and leaves the harnesses on the weekly cron plus dispatch. The
  exposure is that a defect the harnesses would catch can sit on `main` for up to seven days.
- The `changes` job becomes pointless if the clause goes, and should go with it, taking the merge
  to 7.

**Built as the plan specifies. The measurement says the clause is where the money is. One line
either way.**

---

## 6. THE WIRED COUNT, BEFORE AND AFTER

`docs/reviews/check-checkers-are-wired.py`, run on this machine at both trees:

    BEFORE (3c0d648)   Members: 156   WIRED: 77   UNWIRED with a stated reason: 79
    AFTER  (this branch) Members: 156   WIRED: 77   UNWIRED with a stated reason: 79

**Unchanged, which is the point.** The checker parses `jobs.*.steps[].run` across every workflow
file, so moving a step between jobs is invisible to it and only a deleted or renamed invocation
would show. The step count it reports fell from 108 to 98, and that difference is entirely the
twelve per-lane `uv sync --frozen` prologues plus the wiring probe's, minus the one prologue the
merged job keeps and the two new steps this branch adds. No harness invocation lost a flag.

Other checkers that join on this file, all re-run green on this branch (LOCAL):

    check-row-floors.py                rc=0
    check-row-floor-exactness.py       rc=0
    check-no-sigpipe-pipelines.py      rc=0
    probe-ci-checker-steps.py          rc=0
    actionlint 1.7.7, the PINNED TARBALL CI uses, SHELLCHECK_OPTS=--severity=warning   rc=0

The last one is worth naming: `actionlint-py` from pip reports SC2015 at a line CI passes green, so
the tarball at the version and options `ci.yml` itself pins is the only instrument that answers the
question CI asks.

---

## 7. THE #267 RULING, AND WHAT HAPPENED TO probe-273

#267 ruled that the compound lane names must be regenerated in the SAME commit as any repack.
Collapsing twelve lanes into one IS that repack, so those twelve names are **gone rather than
stale** - which discharges the ruling by deletion. No checker enforced them; #267 recorded that its
checker was deferred with a named trigger, and a search of `scripts/` and `docs/reviews/` finds no
lane-name checker to regenerate.

`docs/reviews/probe-273-packing.py:399` selects jobs whose name begins `harness`. **The prefix is
kept** - the merged job is named `Harness assurance - every harness and probe, serial` - so the
probe's selector still finds the population, and every one of the 35 harness step NAMES is
unchanged, which matters because the probe keys its join on the step name and REFUSES on a
duplicate. The two names that now repeat across jobs, `Install uv` and `Install from the frozen
lock`, are both in that file's `WRAP` list and are filtered before the join.

**The probe was NOT edited, and that is a decision rather than an omission.** Its `EXPECT_NAMES = 35`
is an assertion about the THREE HISTORICAL RUNS it reads from the Actions API, where 35 is still
true. Changing it to 38 would break it against its own inputs. Re-run against a run of the NEW
shape it will abort with "population is 38, not 35" - and that abort is the instrument working: it
exists because an earlier version invented 31 durations and summed to 3824s. Re-fitting it needs
runs of the new shape to exist first.

---

## 8. WHAT WAS DELETED, AND WHAT TURNED OUT NOT TO EXIST

**The sharding and packing machinery: there was none to delete.** `grep -i shard` over
`.github/workflows/` and `scripts/` returns nothing. #268 closed as "NOT SHIPPED, and correctly",
so the only artefacts are three records (`MEASURED-268-u3-shard.md`,
`MEASURED-270-exactness-shards.md`, `REPACK-244-under-five.md`) and `probe-273-packing.py`, which
§7 keeps because constraint 3 depends on it.

What was actually deleted is **the twelve-lane fan-out itself**: twelve job definitions, twelve
checkout/uv/setup-python/sync prologues, and the `wiring-probe` job boundary.

**#282 is superseded, not solved.** It asked whether to shard the poles at twelve lanes. The
question dissolves once the harnesses leave the push path, because nothing waits on them: the
median floor of 317s it was fighting is now a weekly serial cost nobody experiences as latency. Its
own record already says "closing 12 needs a sharded run to EXIST" - that run will now never exist,
and should not. **The target disappeared; it was not reached.**

---

## 9. WHAT SERIALISING COSTS, AND THE CONTROL THAT CLOSES IT

Twelve jobs meant twelve disposable checkouts. One job means one tree, so a harness killed mid-row
leaves its mutation in the tree every later step runs against - a green that proves nothing, or a
red pointing at an innocent harness. `scripts/ci-harness-gate.sh` already re-checks its own subject
per invocation; this branch adds the whole-lane assertion that no invocation is the one that does
not, as the LAST step of the job:

    - name: The serial lane left no mutation in src or tests

It writes `git status --porcelain -- src tests` to a file and fails on a non-empty one. It is a
branch inside the step and not an `if:`, for the reason this repository has measured three times.

The other cost is stated rather than hidden: **a failure now stops the lane.** Twelve jobs failed
independently, so one red still reported eleven greens. On a weekly tier that is the right trade;
on the push path it would not be, which is the other half of why the tier moved.

---

## 10. WHAT I COULD NOT MEASURE, AND WHY

**The Assurance tier has not been FIRED on GitHub.** The brief asks for a `workflow_dispatch` proof
that all 29 execute - "a tier nobody can fire is a deleted tier" - and `workflow_dispatch` requires
the workflow to exist on a ref at the remote. The brief also says, last: *do NOT push*. Those two
instructions cannot both be honoured, and the explicit prohibition won.

What was done instead is the strongest local substitute, and it is stronger in one respect and
weaker in another. Stronger: every step of the job was executed end to end, serially, under
GitHub's own shell, so the TALLIES are real rather than predicted. Weaker: it proves nothing about
the trigger wiring - the `if:` expression, the `needs` edge, and the `always()` guard are argued and
`actionlint`-clean, not observed.

**The one thing that must be watched on the first real run** is that `workflow_dispatch` reaches
`harness-assurance` through a SKIPPED `changes` job. That is what `always()` is for, and it is the
exact shape that, got wrong, produces a tier that looks configured and does nothing.

---

## 11. THE READING THAT DECIDES WHETHER THIS IS A WIN

The baseline's own warning applies to every number here: the per-step spread is large - U9's
amputation moved 319s to 211s on unchanged work - so a wall-clock difference smaller than that
spread is not a result.

**This re-tier does not claim a wall-clock result and does not need one.** It claims a BILLING
result, and billing is arithmetic over job counts and ceilings rather than a timing measurement, so
it is not exposed to that spread at all. The wall clock on the push path is expected to be
unchanged for the Gate (same job, same content) and to disappear entirely for the harnesses (they
are no longer on the path).
