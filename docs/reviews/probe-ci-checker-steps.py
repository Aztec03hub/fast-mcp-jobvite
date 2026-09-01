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
still outside what this runs, and the honest reason is not the one
R13 gave. R13 attributed it to `_CHECKER` matching only `check-*.py`.
Measured: the actionlint step is a **32-line block**, so
`classify()` rejects it at the `len(lines) != 1` test, several
filters BEFORE `_CHECKER` is ever consulted. Dropping `_CHECKER`, the
suggested fix, would not have admitted it.

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

**IT DOES NOT RUN EVERYTHING, AND SAYS SO IN NUMBERS.** Of ~78 `run:`
steps only a minority are single-command checker invocations. The rest
are multi-line blocks with their own setup, or they mutate the tree on
purpose - the mutation and control harnesses BREAK their subject to
watch a gate fire, and running those here would edit files under a live
agent.

A probe that quietly skipped those would report a comforting green over
a fraction of the surface. So every skip is counted and categorised, and
the summary states `ran N of M` rather than just `all passed`.
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
_DESTRUCTIVE = re.compile(
    r"ci-harness-gate|amputation|-controls\.sh|probe-|pytest|coverage"
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


def classify(body: str) -> tuple[str, str]:
    """Return (verdict, command-or-reason) for one step body."""
    lines = [
        line.strip()
        for line in body.strip().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if len(lines) != 1:
        return "skip", "multi-line block, has its own setup"
    command = lines[0]
    if not _CHECKER.search(command):
        return "skip", "not a checker invocation"
    if _DESTRUCTIVE.search(command):
        return "skip", "MUTATES THE TREE or costs minutes"
    if _SHELLY.search(command):
        return "skip", "needs shell semantics; not run without a shell"
    return "run", command


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


def actionlint_step() -> tuple[str, list[str], dict[str, str]] | None:
    """The workflow's actionlint invocation, with its env carried over.

    Returned as `(display string, argv, env)`. `None` when no line in
    any step matches - which is itself reportable, because it means
    either the step was removed or this pattern stopped describing it,
    and both must be visible rather than silently reducing the
    population by one.
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
            return line, argv, env
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
    for _, body in all_steps:
        verdict, detail = classify(body)
        if verdict != "run":
            reasons[detail] += 1
            continue
        argv = resolve_argv(detail)
        swapped = argv[: len(_ISOLATED)] == list(_ISOLATED)
        substituted += swapped
        runnable.append((detail, argv, {}, "   [stdlib-only]" if swapped else ""))

    if not runnable:
        print("MATCHED ZERO runnable checker steps out of")
        print(f"{len(all_steps)} run steps. The classifier is broken, not")
        print("the workflow. Exit 2.")
        return 2

    lint = actionlint_step()
    if lint is None:
        reasons["actionlint: no invocation line found in the workflow"] += 1
    elif not pathlib.Path(lint[1][0]).exists():
        reasons[f"actionlint: {lint[1][0]} is not on this machine"] += 1
    else:
        runnable.append((*lint, "   [workflow's own env]"))

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

    print(f"\nRan {len(runnable)} of {len(all_steps)} run steps.")
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
