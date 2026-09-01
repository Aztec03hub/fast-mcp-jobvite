#!/usr/bin/env python3
"""Run CI's checker steps VERBATIM, locally, before pushing.

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


def main() -> int:
    if not WORKFLOW.exists():
        print(f"{WORKFLOW} is missing. Exit 2.")
        return 2

    all_steps = steps()
    if not all_steps:
        print("PARSED ZERO run steps. An empty population reports a clean")
        print("result, which would mean nothing here. Exit 2.")
        return 2

    runnable: list[str] = []
    reasons: Counter[str] = Counter()
    for _, body in all_steps:
        verdict, detail = classify(body)
        if verdict == "run":
            runnable.append(detail)
        else:
            reasons[detail] += 1

    if not runnable:
        print("MATCHED ZERO runnable checker steps out of")
        print(f"{len(all_steps)} run steps. The classifier is broken, not")
        print("the workflow. Exit 2.")
        return 2

    failures: list[tuple[str, int, str]] = []
    for command in runnable:
        # NO `shell=True`. `classify()` has already refused anything
        # carrying shell metacharacters, so `shlex.split` is faithful
        # here - and a probe is the last place to normalise running a
        # string from a file through a shell.
        done = subprocess.run(
            shlex.split(command), cwd=ROOT, capture_output=True, text=True
        )
        if done.returncode == 0:
            print(f"  ok        {command}")
        else:
            print(f"  EXIT={done.returncode:<4} {command}")
            failures.append((command, done.returncode, done.stdout or done.stderr))

    print(f"\nRan {len(runnable)} of {len(all_steps)} run steps, VERBATIM.")
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
