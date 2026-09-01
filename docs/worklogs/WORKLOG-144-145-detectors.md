# WORKLOG #144 + #145 - two detectors that could not see their founding defect

Branch `fix/144-145-detectors`, off `main` at `a824d54`.
Commits: `da848f2` (#144), `fd47e9f` (#145). NOT merged, NOT pushed.

## Both findings are real. Three of the mechanisms behind them are not.

Corrections to the brief and to R13, each measured:

1. **R13's suggested fix for #144 fails the case R13's own table
   names.** "First token after the interpreter not starting with `-`"
   picks `faulthandler` out of `python3 -X faulthandler <checker>`.
   Reinstated verbatim as amputation A2, it fails 2 of the 22 controls.
2. **The brief says a widened regex "still misses `env python3` and
   `/usr/bin/python3`". Both are DETECTED by the regex on main today**,
   because `re.search` finds `python3 ...` as a substring of
   `/usr/bin/python3 ...`. The genuinely missed path-shaped spelling is
   `python3.12`. The brief's conclusion (do not widen) is right; two of
   its four examples are not.
3. **R13's mechanism for the actionlint exclusion is wrong.** R13 blames
   `_CHECKER` at `probe-ci-checker-steps.py:58` and proposes dropping it.
   The actionlint step is a **32-line block**, so `classify()` rejects it
   at `len(lines) != 1` - two filters earlier. Dropping `_CHECKER` would
   not have admitted it.

## #144 - every spelling, and what each detector does with it

Measured by calling `bare_python_steps` directly, before any change.
`*` marks a wrong answer.

| step body | want | old | new |
|---|---|---|---|
| `python3 <yaml-checker>` | fire | fire | fire |
| `python <yaml-checker>` | fire | fire | fire |
| `python3 -u <yaml-checker>` | fire | **silent \*** | fire |
| `python3 -X faulthandler <yaml-checker>` | fire | **silent \*** | fire |
| `python3 -B <yaml-checker>` | fire | **silent \*** | fire |
| `python3.12 <yaml-checker>` | fire | **silent \*** | fire |
| `/usr/bin/python3 <yaml-checker>` | fire | fire | fire |
| `env python3 <yaml-checker>` | fire | fire | fire |
| `python3 <yaml-checker> --self-test` | fire | fire | fire |
| `uv run python <yaml-checker>` | silent | silent | silent |
| `uv run --frozen python <yaml-checker>` | silent | silent | silent |
| `uv run  --frozen python <c>` (2 spaces) | silent | **fire \*** | silent |
| `uv run --frozen python3 <yaml-checker>` | silent | silent | silent |
| `uv run --frozen -- python <yaml-checker>` | silent | **fire \*** | silent |
| `<yaml-checker>` (no interpreter) | silent | silent | silent |
| NEGATIVE: `python3 <stdlib-checker>` | silent | silent | silent |
| NEGATIVE: `python3 -u <stdlib-checker>` | silent | silent | silent |

**Old: 6 wrong of 17. New: 0 wrong of 17.** Four false negatives, two
false positives. The second false positive - `uv run --frozen --` - was
not in R13-L4 and is the same root cause.

### What each control actually proved

22 rows now live in `--self-test`, subjects **derived** from the
population rather than named. Proved live by amputation, because a
control that has never been watched failing proves nothing:

| amputation | rows killed | which |
|---|---|---|
| A1 detector always silent | 12 of 22 | every positive row |
| A2 R13's suggested rule | 2 of 22 | `-X faulthandler`, `python3.12` |
| A3 the original regex | 6 of 22 | the four flag forms, `--`, `uv --` |
| A5 rubber stamp, always fires | 10 of 22 | every negative row |

12 + 10 = 22: **no row is dead weight.**

**The negative arm is what A5 exists to justify.** A1 - a detector that
never fires - passes all ten negative rows. Without A5 those rows would
be unfalsifiable decoration. A5 is the only arm that can see a detector
which has stopped discriminating, and it kills exactly the rows A1
cannot.

**A3 under-reports.** It reinstates the old regex against `" ".join(
tokens)`, and `shlex` has already collapsed the double space, so A3
cannot see the two-space false positive. That case is measured in the
table above, against the real file, not by A3. An instrument artefact,
recorded rather than left to be rediscovered.

## #145 - the decision, and why

**Chosen: make the failure detectable. It was not undetectable.**

The brief offered "state plainly that the class is undetectable locally"
as a legitimate and possibly better answer. It is not available, because
the premise is false. Measured:

    uv run --frozen --isolated --no-project python -c "import yaml"
    -> ModuleNotFoundError: No module named 'yaml'
    python3 -c "import yaml"  -> 6.0.2

So a bare-interpreter step is now run under that isolated interpreter.
It is deliberately **stricter** than the runner rather than equal to it:
a checker that passes only because the runner image happens to ship a
module is relying on a fact nobody promised - which is the same defect
one step earlier, in the words of the neighbouring checker's own advice.

`VERBATIM` is gone from the first line and from the summary. It stopped
being true the moment the interpreter was substituted, and leaving it
would have reproduced this task's own subject one line lower. (It DID
survive my first pass in the summary line; caught by reading the
output.)

### The control R13 asked for, and the one I got wrong first

R13: the probe's red came from a neighbour - `check-checkers-are-wired.py`
is in the runnable set and caught the mutated YAML statically.

**My first control removed that checker and measured nothing.** It is
the same line of `ci.yml` as the step being mutated, so removing it
removes the subject and the arm cannot fail. It went green, which reads
as confirmation. The distinguishing variable is not which step runs but
which interpreter runs it:

| arm | ci.yml | swap | exit | real traceback |
|---|---|---|---|---|
| A | clean | ACTIVE | 0 | no |
| C1 | MUTATED | ACTIVE | 1 | **yes** - the probe's own |
| C2 | MUTATED | AMPUTATED | 1 | no - R13's borrowed red |
| D | restored | ACTIVE | 0 | no |

Committed as `docs/reviews/probe-ci-checker-steps-control.py`, 4/4.
Mutation proved landed and restored **against git**, not a string
compare.

**Its first needle was wrong too.** Searching output for the word
`ModuleNotFoundError` scored C2 as a real traceback - because
`check-checkers-are-wired.py`'s own advice text contains that word. The
search found the documentation of the defect and counted it as the
defect. The needle is now `ModuleNotFoundError: No module named`.

### actionlint: admitted, by a narrow named exception

The invocation line is read **out of the workflow**, so
`SHELLCHECK_OPTS=--severity=warning` travels with it - retyping that
value is the entire mistake being prevented. The block's first six
lines, which `curl` a pinned tarball off GitHub and checksum it, are not
repeated: a pre-push probe that reaches the network on every run is a
worse thing than the gap. When the binary is not where the workflow puts
it, the step is **counted as skipped with that reason**, never silently
dropped.

Population: **12 of 78 steps before, 13 of 78 now**, 10 of the 13 with
the interpreter substituted.

## Gates, each exit code read on its own line

    uv run --frozen ruff check .                      0
    uv run --frozen ruff format --check .             0   117 files
    uv run --frozen mypy                              0   117 files
    check-checkers-are-wired.py                       0
    check-checkers-are-wired.py --self-test           0   26/26
    probe-ci-checker-steps.py                         0   13 of 78
    probe-ci-checker-steps-control.py                 0   4/4 arms
    uv run --frozen pytest                            0   887 passed,
                                                          0 skipped,
                                                          6 deselected

Suite floor derived from `ci.yml`: **887**. Measured 887, so the floor
is exact, not slack.

## What I could NOT settle

- **Whether the isolated interpreter matches the RUNNER's `python3`.** It
  does not, and deliberately so - it is stricter. Whether the GitHub
  runner image ships pyyaml is not something I can measure from here; a
  step relying on that would now show red locally and green in CI. I
  believe that is the correct direction, but it is a judgement, not a
  measurement, and Tier 0 may rule otherwise.
- **Whether `_ACTIONLINT` keeps matching** if the step is rewritten. It
  returns `None` and the probe reports "no invocation line found in the
  workflow" as a counted category rather than quietly shrinking the
  population - but nothing gates that count.

## What I did NOT attempt, kept separate

- Widening the probe to the other 36 multi-line blocks. Out of scope and
  each needs its own judgement about tree mutation.
- The remaining R13 findings (M2-M5, L1-L3, N1-N5). Not in this brief.
- Wiring the new control into CI. It **mutates `ci.yml`**, so it belongs
  with the other `-controls.sh` exemptions, not in a job. It is
  `probe-*`, so it is outside `check-checkers-are-wired.py`'s population
  by construction and needs no exemption entry.

## Tier-2 agents

**Zero spawned.** Every step here was one or two tool calls, and the
protocol says a worker that costs a pane to save a minute is a net loss.
Nothing to `TaskStop`.
