# BRIEF #144 + #145 (TIER 1) — two detectors that cannot see their own founding defect

You are a **Tier-1 sub-orchestrator**. Read
`docs/briefs/PROTOCOL-sub-orchestrators.md` in full and follow it.

## §A — Canon first

Read `docs/briefs/PREAMBLE.md` in full. Read the design at the freeze:

    git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md

Then read `docs/reviews/REVIEW-R13.md` (branch `review/r13`), findings H2
and M1.

## §B — Why these two are ONE piece

I wrote both files today, hours apart, after turning the trunk red twice.
Each was written to catch a specific failure. **Neither can catch it.**
Same root shape: a detector built from the one spelling I happened to have
shipped, and a control that passed for a reason other than the one
claimed. Fixing them separately would fix the instances and leave the
shape.

## §C — #144 (H2): `bare_python_steps` misses one interpreter flag

In `docs/reviews/check-checkers-are-wired.py`. `_BARE_PYTHON` uses
`python3?\s+\S*?(?P<name>check-[\w-]+\.py)`. `\S*?` cannot cross a space:

    python3 -u docs/reviews/check-x.py               NOT detected
    python3 -X faulthandler docs/reviews/check-x.py  NOT detected
    python3 docs/reviews/check-x.py                  detected

This is the function whose docstring says *"THIS EXISTS BECAUSE I SHIPPED
EXACTLY THIS AND TURNED main RED."*

**DO NOT widen the regex.** Adding `-\w+\s+` still misses
`-X faulthandler` (flag with an argument), `env python3`,
`/usr/bin/python3`, `python3.12`. That is the pattern-shaped fix this
repo has been bitten by repeatedly.

**Walk tokens instead**: `shlex.split` the step body, find the interpreter
token, take the first non-flag token after it. That also kills **R13-L4**
free — `uv run  --frozen` with two spaces is currently a FALSE POSITIVE,
because the lookbehind is a literal single-spaced string — and removes
both variable-width lookbehinds, which cannot be written correctly in
Python's `re` and are why both bugs exist.

**Controls required, one per spelling, and a NEGATIVE arm**: a stdlib-only
checker invoked bare must still NOT fire. A detector that flags everything
is as useless as one that flags nothing, and only the negative arm
separates them.

## §D — #145 (M1): a probe that cannot see either failure it names

`docs/reviews/probe-ci-checker-steps.py` claims to run CI's steps verbatim
so that two specific failures cannot recur. R13 measured that it catches
neither:

1. **The actionlint threshold (false RED).** `_CHECKER` matches only
   `check-*.py`, so the actionlint step is never a candidate — that case
   is outside the population entirely.
2. **Bare `python3` (the false GREEN that broke main).** The probe runs
   `python3 .../check-*.py` with the LOCAL interpreter, which has pyyaml.
   It reproduces the false green by construction.

**AND THE CONTROL THAT SEEMED TO PROVE IT WORKS IS THE SHARPEST PART.**
R13 mutated `ci.yml` back to the known-bad form; the probe exited 1 — for
the wrong reason. `check-checkers-are-wired.py` is one of the twelve
commands it runs, and *its* static detector caught the mutated YAML. No
`ModuleNotFoundError` occurred and none could. Remove that one checker
from the runnable set and the probe is blind.

**Your options, and you choose with reasons — I will not pre-rule this:**
- widen the population to every step it can safely repeat, carrying each
  tool's env (`SHELLCHECK_OPTS`) out of the workflow rather than retyping
  it, which is the probe's whole point; and/or
- accept that interpreter-availability is undetectable locally **by
  construction** and say so in the docstring instead of implying coverage.

**Whichever you choose, the current docstring overclaims and must be
corrected IN PLACE** — it presents the probe as the answer to two named
failures it cannot see. Do not append a rider; rewrite the claim.

## §E — What you must not do

- **Do not merge, do not push.** I do both.
- Do not `git stash`. Two other worktrees are live.
- No `Co-Authored-By` or "Generated with" trailer. `git commit -F` with a
  **quoted** heredoc.
- Do not let a Tier-2 worker decide whether a control is vacuous.
- `check-checkers-are-wired.py` is WIRED. If your change would make it red
  on this tree, stop and report rather than landing a red gate.

## §F — Budget

At most **2** Tier-2 agents at once (`model: "sonnet"`, or `"haiku"` for
anything verifiable at a glance). Close each with `TaskStop` the moment
its result is in hand AND committed on your branch. Do not spawn one for
work you could do in a single tool call.

## §G — Report

`SendMessage` to `team-lead`: the spellings you measured and which the old
and new detectors catch, what each control proved, your decision on #145
with its reasoning, every gate exit code on its own line, and what you
could not settle — kept separate from what you did not attempt.

**If either finding is wrong, say so.** They came from a review that also
corrected a number in one of my docstrings, and it was right.
