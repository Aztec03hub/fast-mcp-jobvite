#!/usr/bin/env python3
"""Run CI's checker steps locally, before pushing.

    uv run --frozen python docs/reviews/probe-ci-checker-steps.py

**WHY THIS EXISTS.** On 2026-09-01 I turned the trunk red twice in one
day by running a command that RESEMBLED CI's instead of CI's:

- `actionlint` bare, where CI runs it with
  `SHELLCHECK_OPTS=--severity=warning`. The bare run reported SC2015
  on a line whose own comment explains why it is correct, and I began
  writing it up as a defect. **A false RED, manufactured out of a
  configuration difference.**
- A step wired as `python3 docs/reviews/check-checkers-are-wired.py` but
  tested with `uv run --frozen python ...`. My `python3` had pyyaml, the
  runner's did not, and it died with `ModuleNotFoundError` on the commit
  that wired it. **A false GREEN.**

Both directions, same root cause, same day. So this stops retyping
commands and executes the strings in the workflow.

**AND FOR ITS FIRST DAY IT COULD SEE NEITHER OF THEM.** Review R13
measured that, and the finding is the reason this paragraph replaced a
claim rather than sitting under it. Both halves were real:

*The false GREEN was reproduced BY CONSTRUCTION.* Running
`python3 <checker>` with the local `python3` is the exact act that
produced the failure - my `python3` has pyyaml. The probe re-ran the
author's lucky environment and called the result CI's.

*And the control that seemed to prove otherwise was passing for
someone else's reason.* R13 mutated `ci.yml` back to the bad form and
this probe exited 1 - because `check-checkers-are-wired.py` is one of
the commands it runs, and THAT checker caught the mutated YAML
statically. No `ModuleNotFoundError` occurred and none could. Take
that one neighbour out of the runnable set and the probe was blind. A
green supplied by a different gate is not this gate working.

So a step written with a bare interpreter is now run under
`uv run --frozen --isolated --no-project python`, which resolves to
the standard library and nothing else - measured: it raises
`ModuleNotFoundError: No module named 'yaml'` where the local
`python3` imports pyyaml 6.0.2. That is a STRICTER environment than
the runner, not an identical one, and deliberately so: a checker that
passes only because the runner image happens to ship a module is
relying on a fact nobody promised, which is the same defect one step
earlier. **This is why the word VERBATIM came out of the first line.**
The command is the workflow's; the interpreter under it is chosen.

The proof is the amputation, not the assertion: with
`check-checkers-are-wired.py` REMOVED from the runnable set and
`ci.yml` mutated to the bad form, this probe still exits 1, now on a
`ModuleNotFoundError` it raised itself.

## The actionlint case is NOT covered, and that is a gap, not a design

The first failure above - `actionlint` at the wrong severity - is
outside what `classify()` admits, and the reason has CHANGED since
this paragraph was first written, so it is restated rather than left
standing. R13 attributed the miss to `_CHECKER` matching only
`check-*.py`. That was wrong then: the step is a 32-line block and
`classify()` rejected it at the `len(lines) != 1` test, several
filters before `_CHECKER` was ever consulted. It is right NOW. Since
#147 opened the blocks up, `classify_block()` reaches the selector
and rejects the step because it holds no `check-*.py` line - R13's
diagnosis became true of the code a day after it was measured false
of it, which is the strongest reason not to leave a superseded
explanation in place next to a corrected one.

It is admitted here by a narrow, named exception instead: the
invocation line is read OUT OF THE WORKFLOW, so `SHELLCHECK_OPTS`
travels with it rather than being retyped into this file - retyping it
is the entire mistake being prevented. What is not repeated is the
block's first six lines, which `curl` a pinned tarball off GitHub and
checksum it; a pre-push probe that reaches the network on every run is
a different and worse thing. So the binary is used where the workflow
puts it, and when it is not there the step is COUNTED AS SKIPPED with
that reason. A silent skip here would be the failure this file's own
summary section exists to prevent.

**IT IS A PROBE, NOT A GATE, AND THE NAME IS LOAD-BEARING.**
`check-checkers-are-wired.py` enumerates `docs/reviews/check-*.py` and
requires every member to be wired or carry a stated exemption. A file
named `check-*` here would have to be wired into CI - where it would
re-run, inside CI, the steps CI is already running. `probe-*` keeps it
out of that container, which is the correct answer rather than a dodge.

## What it refuses to run, and why that is the honest part

**IT DOES NOT RUN EVERYTHING, AND SAYS SO IN NUMBERS.** Every skip is
counted and categorised, and the summary states `ran N of M` rather
than `all passed`. A probe that quietly skipped would report a
comforting green over a fraction of the surface.

**AND UNTIL #147 THE BIGGEST CATEGORY WAS A LIE ABOUT WHY.** 34 of 78
steps were filed under `multi-line block, has its own setup`, and that
bucket was not a random 34. **A step is a multi-line block PRECISELY
BECAUSE it carries a flag, an env var, or `|| exit 1` handling - and a
flag is exactly what makes CI's invocation differ from the bare local
one.** The twelve steps this probe could run verbatim were single-line,
no-argument invocations: the case that cannot go wrong that way. So the
selection was biased towards the steps that cannot differ, and away
from the steps that can. It proved it: it could not run
`Committed file types, whole tree`, the step that refused the tree for
127 commits, and the disclaimer below - *a green from this probe
licenses only what it executed* - was true but far weaker than it read.

That bucket is now EMPTY, and it was emptied by reading the blocks, not
by loosening `_SHELLY`. Three shapes are recognised:

- a backslash CONTINUATION is joined, because a command split over two
  physical lines was never a block with setup at all;
- `set -uo pipefail` + one invocation + a trailing
  `|| { echo ...; exit 1; }` is RUN, because a guard that only prints
  and exits nonzero leaves the exit code where the invocation put it;
- `out=$(<invocation> 2>&1); rc=$?` followed by assertions on `$out` is
  LIFTED: the invocation runs, the STEP IS NOT COVERED, and the two are
  counted in different buckets. R14's H-1 is what that separation is
  for.

What is left is left WITH ITS REASON, and both reasons are real. Four
steps drive a harness that EDITS the document it gates. Two steps
tolerate a nonzero exit on purpose - `check-clause-citations.py` and
`check-standards-citations.py` exit 2 when the private standards
sibling is absent, which is the normal local state - so lifting their
invocation would manufacture a false RED out of a configuration
difference, the first failure in this file's own opening.
"""

from __future__ import annotations

import os
import pathlib
import re
import shlex
import subprocess
import sys
from collections import Counter

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

#: A checker invocation this probe can safely repeat.
_CHECKER = re.compile(r"(?:docs/reviews|scripts)/check-[\w-]+\.py")

#: Commands that MUTATE THE TREE to watch a gate fire, or that cost
#: minutes. Never run from here: an agent may be working in this
#: checkout, and a harness that edits a source file to prove a test dies
#: is not something to trigger as a side effect of a pre-push check.
#:
#: `-controls\.py`, `--controls` and `-sweep\.py` were ADDED when the
#: multi-line blocks were opened up (#147). Until then this list only
#: had to cover twelve single-line steps, none of which reached a
#: mutating harness. `check-coupling-controls.py`,
#: `check-coupling-sweep.py` and `check-obligations.py --controls` all
#: EDIT the document they gate and re-check it after - their CI steps
#: grep for `post-run re-check of the real DESIGN.md: exit=0`. They
#: were unreachable before and are reachable now, so the list grew
#: with the reach. A deny-list that is correct only for the set it
#: was written against is the defect this file is about.
_DESTRUCTIVE = re.compile(
    r"ci-harness-gate|amputation|-controls\.(?:sh|py)|(?:^|\s)--controls(?:\s|$)"
    r"|-sweep\.py|probe-|pytest|coverage"
)


#: Shell metacharacters. A command carrying any of these needs a shell
#: to mean what CI means, and this probe refuses to run it rather
#: than reach for `shell=True` on a string read out of a file.
_SHELLY = re.compile(r"""[|&;<>()$`\\"'*?\[\]~]""")

#: A token that IS a bare interpreter, by basename.
_BARE_INTERPRETER = re.compile(r"^python(?:\d+(?:\.\d+)*)?$")

#: What a bare interpreter is REPLACED WITH here. Not the local
#: `python3`: that is the environment whose lucky pyyaml produced the
#: false green in the first place, so running under it reproduces the
#: failure instead of detecting it.
_ISOLATED = ("uv", "run", "--frozen", "--isolated", "--no-project", "python")

#: The workflow's own actionlint invocation, matched so that the env
#: prefix comes with it. `SHELLCHECK_OPTS` must travel from the
#: workflow; a copy typed into this file is the defect, not the fix.
_ACTIONLINT = re.compile(
    r"^(?P<env>(?:\w+=\S+\s+)*)(?P<bin>\S*actionlint)\s+(?P<args>.*)$"
)


def steps() -> list[tuple[str, str]]:
    """Every `jobs.*.steps[].run` in ci.yml, as (step name, body)."""
    loaded = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    out: list[tuple[str, str]] = []
    for job in (loaded.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            if isinstance(step, dict) and isinstance(step.get("run"), str):
                out.append((step.get("name", "(unnamed)"), step["run"]))
    return out


#: THE BUCKET #147 EMPTIED. It read "multi-line block, has its own
#: setup" and held 34 steps, and it was not a random 34: a step is a
#: block PRECISELY BECAUSE it carries a flag or `|| exit 1` handling,
#: which is what makes CI's invocation differ from a bare local one.
#: It is kept as a name so the control can amputate back to it.
_MULTILINE_REASON = "multi-line block, has its own setup"

#: NOT "not a checker invocation" any more, because that sentence was
#: read as "this step is not a gate" and thirteen of these steps are
#: gates - they run `check-*.sh` harnesses through
#: `scripts/ci-harness-gate.sh`. `_CHECKER` matches `.py` only, so
#: what the bucket actually means is "nothing in this step matches
#: THIS PROBE'S selector", and it now says so. Widening the selector
#: to `.sh` is #153's family and is deliberately not done here.
_NO_CHECKER_REASON = "no check-*.py invocation in the step (this probe's selector)"
_LIFTED_REASON = "multi-line block, ONE LINE LIFTED and run (the step is not covered)"

#: `set -uo pipefail`, `set -euo pipefail`, `set +e`. Shell options and
#: NOTHING else - anchored at both ends, and a sign followed by at
#: least one letter is required, so `set -- "$@"` (which changes the
#: positional parameters, and is NOT inert) does not match and is not
#: discarded.
#:
#: **The first version of this was `^set [+-][a-zA-Z]+$` and it silently
#: matched nothing.** Every `set` line in this workflow is
#: `set -uo pipefail` - a flag AND an option name - so the guard dropped
#: no line, the block never reduced to a single command, and
#: `Committed file types, whole tree` came out as "the shell around the
#: invocation is not trivial". The exact step this task exists for was
#: still skipped, now with a NEW and more convincing reason. A filter
#: that matches nothing gives every input the same verdict, and that
#: verdict reads like a finding.
_SET_FLAGS = re.compile(r"^set\s+[+-][a-zA-Z]+(?:\s+[a-zA-Z]+)*$")

#: `cmd || { echo ...; exit 1; }` - the whole tail from the `||` on.
_GUARD_OPEN = re.compile(r"\|\|\s*\{")

#: `out=$(cmd 2>&1); rc=$?` - the capture form. The invocation is real
#: and repeatable; the ASSERTIONS that follow it in the block are not
#: reproduced here, which is why this yields a LIFT and never a RUN.
_CAPTURE = re.compile(r"^\w+=\$\((?P<cmd>.+?)\)\s*;\s*\w+=\$\?$")

#: `[ "$rc" -eq 2 ]` - a block that treats a NONZERO exit as success.
#: Two steps do (`check-clause-citations.py` and
#: `check-standards-citations.py` exit 2 when the private standards
#: sibling is absent, which is the normal local state and the runner's
#: state too). Lifting the invocation out of one of those turns CI's
#: deliberate green into a probe red - a false RED manufactured out of a
#: configuration difference, which is the FIRST failure in this file's
#: own docstring. So these stay counted, with that as the reason.
_TOLERATES_NONZERO = re.compile(r'\$rc"?\s+-eq\s+[1-9][0-9]*')

#: A guard body statement that cannot change an exit code: it prints, or
#: it exits nonzero on a path the invocation already failed.
_INERT_GUARD_STATEMENT = re.compile(r"^(?:echo\b|printf\b|exit\s+[1-9][0-9]*)")


def significant(body: str) -> list[str]:
    r"""The body's real lines, continuations joined.

    Blanks and comments are dropped, and a backslash CONTINUATION is
    joined to the line it continues.

    **The join is a bug fix, not a convenience.** `classify()` counted
    physical lines, so `bash scripts/ci-harness-gate.sh check-x.sh \\`
    plus its flags read as a two-line block "with its own setup" when it
    is one command with no setup at all. Fourteen steps in `ci.yml` are
    that shape, and every one of them was filed under a reason that was
    not true of it. A wrong reason in the skip table is worse than a
    skip: it tells the reader the step is unrunnable for a structural
    cause when the real cause is how this file counted newlines.
    """
    out: list[str] = []
    pending = ""
    for raw in body.strip().splitlines():
        line = raw.strip()
        if pending:
            line = f"{pending} {line}"
            pending = ""
        elif not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            pending = line[:-1].rstrip()
            continue
        out.append(line)
    if pending:
        out.append(pending)
    return out


def _fold_guards(lines: list[str]) -> list[str]:
    """Fold `cmd || {` and its following lines into one logical line."""
    out: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if _GUARD_OPEN.search(line) and not line.rstrip().endswith("}"):
            while index < len(lines):
                line = f"{line} {lines[index]}"
                closed = lines[index].rstrip().endswith("}")
                index += 1
                if closed:
                    break
        out.append(line)
    return out


def _guard_is_inert(tail: str) -> bool:
    """Whether a `|| { ... }` tail can only report, never rescue.

    A guard that echoes and exits nonzero leaves the step's exit code
    exactly where the invocation put it, so running the invocation alone
    reproduces the step. A guard that runs anything else - a retry, a
    fallback, an `exit 0` - does not, and this returns False for it
    rather than guessing.
    """
    tail = tail.strip()
    if not (tail.startswith("{") and tail.endswith("}")):
        return False
    inner = tail[1:-1]
    statements = [part.strip() for part in inner.split(";") if part.strip()]
    return bool(statements) and all(
        _INERT_GUARD_STATEMENT.match(part) for part in statements
    )


def classify_command(command: str) -> tuple[str, str]:
    """Verdict for a step that is ONE command."""
    if not _CHECKER.search(command):
        return "skip", _NO_CHECKER_REASON
    if _DESTRUCTIVE.search(command):
        return "skip", "MUTATES THE TREE or costs minutes"
    if _SHELLY.search(command):
        return "skip", "needs shell semantics; not run without a shell"
    return "run", command


def classify_block(lines: list[str]) -> tuple[str, str]:
    """Verdict for a step that is a multi-line block.

    **THIS IS THE WHOLE POINT OF #147.** The block bucket was not a
    random remainder. A step is a block PRECISELY BECAUSE it carries a
    flag, an env var or `|| exit 1` handling - and a flag is exactly
    what makes CI's invocation differ from the bare local one. So the
    steps this file could run verbatim were the ones that cannot go
    wrong that way, and the ones it refused were the ones that can. It
    refused `Committed file types, whole tree`, the step that held the
    trunk red for 127 commits, for that reason and no other.

    Returns `run` only when running the extracted invocation alone
    reproduces the step's exit code. When the block also ASSERTS on the
    checker's output, the verdict is `lift`: the invocation is run, the
    step is NOT covered, and the two are counted separately - R14's H-1
    is what that separation is for.
    """
    body = _fold_guards([line for line in lines if not _SET_FLAGS.match(line)])
    hits = [line for line in body if _CHECKER.search(line)]
    if not hits:
        return "skip", _NO_CHECKER_REASON
    if len(hits) > 1:
        return "skip", f"multi-line block: {len(hits)} checker lines, none is THE one"
    line = hits[0]
    if _DESTRUCTIVE.search(line):
        return "skip", "MUTATES THE TREE or costs minutes"
    if any(_TOLERATES_NONZERO.search(part) for part in body):
        return "skip", "multi-line block: a NONZERO exit is tolerated by the step"

    if body == [line]:
        head, sep, tail = line.partition("||")
        if not sep:
            return classify_command(line)
        if _guard_is_inert(tail):
            return classify_command(head.strip())
        return "skip", "multi-line block: the `||` tail is not a bare report-and-die"

    match = _CAPTURE.match(line)
    if match:
        inner = match.group("cmd").removesuffix("2>&1").strip()
        verdict, detail = classify_command(inner)
        return ("lift", detail) if verdict == "run" else (verdict, detail)
    return "skip", "multi-line block: the shell around the invocation is not trivial"


def classify(body: str) -> tuple[str, str]:
    """Return (verdict, command-or-reason) for one step body."""
    lines = significant(body)
    if len(lines) == 1:
        return classify_command(lines[0])
    return classify_block(lines)


def resolve_argv(command: str) -> list[str]:
    """The argv to actually execute for one workflow command.

    A bare interpreter is swapped for the isolated one. Everything
    else runs exactly as the workflow spells it, `uv run --frozen`
    included - those steps already name the environment they want.
    """
    argv = shlex.split(command)
    if argv and _BARE_INTERPRETER.match(pathlib.PurePath(argv[0]).name):
        return [*_ISOLATED, *argv[1:]]
    return argv


def actionlint_step() -> tuple[str, list[str], dict[str, str], str] | None:
    """The workflow's actionlint invocation, with its env carried over.

    Returned as `(display string, argv, env, the skip bucket its step
    was counted in)`. `None` when no line in any step matches - which is
    itself reportable, because it means either the step was removed or
    this pattern stopped describing it, and both must be visible rather
    than silently reducing the population by one.

    The fourth element is what keeps the arithmetic honest: the caller
    moves the step OUT of that bucket and into the lifted one, and it
    has to be told which bucket rather than assuming.
    """
    for _, body in steps():
        for raw in body.splitlines():
            line = raw.strip()
            if "actionlint" not in line or line.startswith("#"):
                continue
            match = _ACTIONLINT.match(line)
            if not match:
                continue
            env = dict(
                pair.split("=", 1) for pair in match.group("env").split() if "=" in pair
            )
            argv = [match.group("bin"), *shlex.split(match.group("args"))]
            verdict, bucket = classify(body)
            if verdict != "skip":
                # The step is already RUN in its own right, so lifting a
                # line out of it would count it twice. Refuse rather
                # than adjust a bucket it is not in.
                return None
            return line, argv, env, bucket
    return None


def main() -> int:
    if not WORKFLOW.exists():
        print(f"{WORKFLOW} is missing. Exit 2.")
        return 2

    all_steps = steps()
    if not all_steps:
        print("PARSED ZERO run steps. An empty population reports a clean")
        print("result, which would mean nothing here. Exit 2.")
        return 2

    runnable: list[tuple[str, list[str], dict[str, str], str]] = []
    reasons: Counter[str] = Counter()
    substituted = 0
    lifted = 0
    for _, body in all_steps:
        verdict, detail = classify(body)
        if verdict == "skip":
            reasons[detail] += 1
            continue
        argv = resolve_argv(detail)
        swapped = argv[: len(_ISOLATED)] == list(_ISOLATED)
        substituted += swapped
        note = "   [stdlib-only]" if swapped else ""
        if verdict == "lift":
            # THE STEP IS NOT COVERED AND MUST NOT BE COUNTED AS IF IT
            # WERE. The block runs this invocation and then asserts on
            # its OUTPUT - that the checker reported a non-zero number
            # of mappings, that a sweep printed `0 escapes are holes`.
            # None of those assertions happen here. Running the
            # invocation proves the checker exits 0; it does not prove
            # the step would pass.
            lifted += 1
            reasons[_LIFTED_REASON] += 1
            note = f"{note}   [LIFTED; step not covered]"
        runnable.append((detail, argv, {}, note))

    if not runnable:
        print("MATCHED ZERO runnable checker steps out of")
        print(f"{len(all_steps)} run steps. The classifier is broken, not")
        print("the workflow. Exit 2.")
        return 2

    # THE ACTIONLINT LINE IS LIFTED OUT OF A STEP THAT `classify()` HAS
    # ALREADY COUNTED AS SKIPPED, so admitting it without adjusting that
    # bucket counts one step TWICE (R14 review, H-1). It made
    # `13 + 36 + 29 + 1 = 79` out of 78 steps, and the imbalance was the
    # only visible symptom of a subtler thing: **lifting one LINE out of
    # a multi-line block does not make that STEP covered.** Honest step
    # coverage did not move from 12; a line inside step 13 is now run.
    # So the lifted line gets its OWN category rather than being folded
    # into the ran-count's justification.
    #
    # THE BUCKET IT COMES OUT OF IS NOW ASKED FOR, NOT ASSUMED. This
    # decremented `_MULTILINE_REASON` by name until #147, which was true
    # only while every multi-line block landed in that one bucket. It no
    # longer does - the actionlint block holds no `check-*.py` line at
    # all, so it now lands in `not a checker invocation` - and a
    # hard-coded decrement of the wrong bucket would have driven that
    # count NEGATIVE while the total still balanced. A constant that was
    # right about a population is exactly what stops being right when
    # the population is re-cut.
    lint = actionlint_step()
    if lint is None:
        reasons["actionlint: no invocation line found in the workflow"] += 1
    elif not pathlib.Path(lint[1][0]).exists():
        reasons[f"actionlint: {lint[1][0]} is not on this machine"] += 1
    else:
        line, argv, env, bucket = lint
        runnable.append((line, argv, env, "   [workflow's own env]"))
        lifted += 1
        reasons[bucket] -= 1
        reasons[_LIFTED_REASON] += 1

    failures: list[tuple[str, int, str]] = []
    for command, argv, env, note in runnable:
        # NO `shell=True`. `classify()` has already refused anything
        # carrying shell metacharacters, so `shlex.split` is faithful
        # here - and a probe is the last place to normalise running a
        # string from a file through a shell.
        done = subprocess.run(  # noqa: S603
            argv,
            cwd=ROOT,
            capture_output=True,
            text=True,
            env={**os.environ, **env} if env else None,
        )
        if done.returncode == 0:
            print(f"  ok        {command}{note}")
        else:
            print(f"  EXIT={done.returncode:<4} {command}{note}")
            failures.append((command, done.returncode, done.stdout or done.stderr))

    # THE IDENTITY CHECK THAT WOULD HAVE CAUGHT H-1. Every step is
    # either run or accounted for by exactly one reason. If these
    # disagree the categories overlap or leak, and every number
    # printed below is untrustworthy - so refuse, do not print them.
    accounted = len(runnable) - lifted + sum(reasons.values())
    if accounted != len(all_steps):
        print(
            f"\nCATEGORIES DO NOT BALANCE: {len(runnable)} run"
            f" (of which {lifted} lifted from a skipped step)"
            f" + {sum(reasons.values())} skipped = {accounted},"
            f" but there are {len(all_steps)} run steps."
        )
        print("A step is being counted twice or not at all. Exit 2.")
        return 2

    print(
        f"\nRan {len(runnable)} of {len(all_steps)} run steps in {WORKFLOW.name} ONLY."
    )
    print(
        f"{substituted} of them had a bare interpreter SUBSTITUTED for a "
        "stdlib-only\none, so the command is the workflow's and the "
        "interpreter under it is not.\nThat substitution is the point: the "
        "local `python3` has the module whose\nabsence on the runner is the "
        "failure being hunted."
    )
    print("Not run, by category:")
    for reason, count in reasons.most_common():
        print(f"  {count:3d}  {reason}")

    if failures:
        print(f"\n{len(failures)} step(s) that CI runs FAIL here:")
        for command, code, output in failures:
            print(f"\n  $ {command}   -> exit {code}")
            for line in output.strip().splitlines()[-6:]:
                print(f"      {line}")
        return 1

    print(
        "\nEvery step this probe ran is green. That is a claim about "
        f"{len(runnable)} steps,\nNOT about CI: the majority are not run "
        "here, and a green from this\nprobe licenses only what it executed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
