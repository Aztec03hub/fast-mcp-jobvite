#!/usr/bin/env python3
"""Every checker in `docs/reviews/` runs in CI, or says why it does not.

    python3 docs/reviews/check-checkers-are-wired.py
    python3 docs/reviews/check-checkers-are-wired.py --self-test

**WHY THIS EXISTS.** Three checkers here were written, measured,
committed - and never wired into CI. Nothing said so. They sat green and
inert while being cited as gates, which is strictly worse than not
having them: an unwired checker is a claim of coverage that costs
nothing to make and nobody can see is false.

**IT IS THE SAME MISTAKE TWICE, WITH THE SAME INSTRUMENT.** The obvious
census is `grep <basename> .github/workflows/ci.yml`. That counts a name
in a COMMENT as wired. Review R12 used it and mislabelled three files; I
used it earlier the same day and reported
`check-design-citation-shape.py` as WIRED, then spent hours calling an
unwired scan a gate. My replacement parser was ALSO wrong: it matched
only block-form `run: |` and missed every single-line `run:`, reporting
`check-coupling.py` as unwired twenty minutes after I had read its step.
The contradiction between two wrong instruments is the only reason
either was caught.

So this file does not grep the workflow. It **parses the YAML** and
reads `jobs.*.steps[].run` - the only place a step can actually execute
- and strips shell comments from those bodies before looking for a name.

**THE EXEMPTION IS A DECISION, NOT A HOLE.** A checker may be unwired on
purpose: `check-review-coverage.py` reports a real backlog and exits 1
until that backlog clears. Being unwired is fine. Being unwired *and
unrecorded* is the defect. So an exemption needs a non-empty reason, and
a blank one is refused.

**IT ALSO CHECKS THE REVERSE, which nothing else here does.** An
exemption naming a checker that IS wired is stale - the reason has
outlived the condition, and a stale exemption is how a list stops
describing the thing it lists. That is a failure too, not a nit.

## Scope, stated rather than assumed

The container is `docs/reviews/check-*.py` and
`docs/reviews/check-*.sh`, enumerated from git. It deliberately does NOT
include `scripts/check-*.sh` - those are the per-unit mutation and
control HARNESSES, and they reach CI through
`scripts/ci-harness-gate.sh` (32 call sites in `ci.yml`), which is its
own container with its own gate. Two different populations with two
different wiring mechanisms; conflating them would make this checker
report on files it cannot judge.

**WHAT IT CANNOT DO.** It proves a checker is INVOKED, not that its exit
code gates the job. A step that runs a checker and swallows its status
reads as WIRED here. That is a real gap, and the four non-gating
shell forms this repo has shipped are the reason to say so out loud
rather than let "wired" imply "gating".
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

#: Checkers that are deliberately not wired, each with the reason. **A
#: bare name is refused: the reason IS the exemption**, the same shape
#: `check-no-errexit.py` and `check-settings-are-read.py` use.
UNWIRED_BY_DECISION: dict[str, str] = {
    "check-review-coverage.py": (
        "reports a real backlog of trunk commits no review round covered "
        "and exits 1 until it clears. Wiring it now lands a permanently "
        "red gate, which this repo has twice proved people learn to "
        "ignore. Wire it when the count reaches zero - task #119."
    ),
    "check-row-floor-control.sh": (
        "a control OF a control: it proves `check-row-floors.py` can still "
        "fail, by breaking a floor on purpose. Running it in CI would "
        "mutate the tree mid-job. Invoked by hand when the floor checker "
        "changes."
    ),
    "check-row-floor-controls.sh": (
        "the plural sibling of the above, same reason: it mutates floors "
        "to watch the checker fire. A control that must break its subject "
        "cannot share a job with the subject."
    ),
    "check-harness-result-controls.sh": (
        "proves `check-harness-result.sh` rejects malformed HARNESS-RESULT "
        "lines by feeding it malformed ones - it must break its subject, "
        "so it cannot share a job with it. Run by hand when the canonical "
        "line changes; 8/8 controls fire as of 2026-09-01."
    ),
}

#: `check-design-citation-shape.py` was here, exempted while #126's 47
#: blank-END citations were swept. The sweep landed, it went green, it
#: was wired, and this entry was deleted in the same commit. That is the
#: exemption working as designed: a reason with a stated end condition,
#: removed when the condition ended rather than left to rot. Had it been
#: left, the stale-exemption check below would have failed the build -
#: which is the point of checking the reverse direction.


def _reasons_are_non_empty() -> None:
    """A blank reason is not an exemption."""
    blank = [k for k, v in UNWIRED_BY_DECISION.items() if not v.strip()]
    if blank:
        raise SystemExit(f"blank exemption reason(s): {blank}")


def checkers() -> list[str]:
    """Basenames of every checker in `docs/reviews/`, from git.

    Enumerated from the CONTAINER, never a hand-kept list beside it -
    a list maintained next to the thing it describes is blind to the
    member nobody added, which is how three checkers went unwired.
    """
    done = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "docs/reviews/check-*.py",
            "docs/reviews/check-*.sh",
        ],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        print(f"git ls-files failed: {done.stderr.strip()}")
        print("This is a BROKEN INSTRUMENT, not a finding. Exit 3.")
        raise SystemExit(3)
    #: THIS FILE IS IN ITS OWN POPULATION, deliberately - a checker that
    #: exempts itself from its own container is the precise blind spot
    #: it exists to catch. **That is ASSERTED by control 4, not claimed
    #: here**, because this comment was INERT when it was written: git
    #: lists only TRACKED files, the checker was still untracked, and it
    #: excluded itself for a reason no line of code mentions. The census
    #: read 26 and became 27 on the commit that tracked it.
    return sorted(pathlib.PurePath(p).name for p in done.stdout.split())


def strip_comments(body: str) -> str:
    """Drop shell comments, so a `#` line does not read as wired.

    This is the exact false positive that mislabelled three checkers
    twice. The rule is deliberately blunt: from an unquoted `#` to end
    of line. A `#` inside a quoted string would be over-stripped, which
    can only ever cause a FALSE 'unwired' - the safe direction for a
    gate whose job is to find things nobody wired.
    """
    return re.sub(r"(?m)(?<!\$)#.*$", "", body)


#: A step body that invokes a checker with the interpreter that has only
#: the standard library. `uv run ...` reaches the project environment;
#: a bare `python3 docs/reviews/x.py` does not.
_BARE_PYTHON = re.compile(
    r"(?<!uv run )(?<!uv run --frozen )python3?\s+\S*?(?P<name>check-[\w-]+\.py)"
)

#: `import x` / `from x import ...` at the start of a line - top-level
#: imports only, which is where an unavailable module kills the process.
_IMPORT = re.compile(r"^(?:import|from)\s+([\w.]+)", re.MULTILINE)


def third_party_imports(name: str) -> list[str]:
    """Modules a checker imports that the stdlib does not ship.

    Local-only names are excluded: this asks what a BARE interpreter
    would fail to find, not what is merely unusual.
    """
    path = ROOT / "docs" / "reviews" / name
    if not path.exists() or path.suffix != ".py":
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    found = {m.group(1).split(".")[0] for m in _IMPORT.finditer(text)}
    return sorted(
        mod
        for mod in found
        if mod not in sys.stdlib_module_names and mod != "__future__"
    )


def bare_python_steps(text: str) -> list[tuple[str, list[str]]]:
    """Checkers run by a bare interpreter that need more than stdlib.

    **THIS EXISTS BECAUSE I SHIPPED EXACTLY THIS AND TURNED main RED.**
    Every other checker in `docs/reviews/` is stdlib-only, so the family
    convention is `run: python3 ...`. This one imports `yaml`; I tested
    it with `uv run`, wired it as `python3`, and my local `python3`
    happened to have pyyaml while the runner's did not. It died with
    `ModuleNotFoundError` on the commit that wired it.

    A convention that is safe for every existing member is not safe for
    the member that breaks the assumption the convention rests on.
    """
    problems: list[tuple[str, list[str]]] = []
    for match in _BARE_PYTHON.finditer(text):
        name = match.group("name")
        needed = third_party_imports(name)
        if needed:
            problems.append((name, needed))
    return problems


def run_bodies() -> tuple[str, int]:
    """Every `jobs.*.steps[].run` in every workflow, comment-stripped.

    Returns the concatenated text and the number of run steps seen. The
    count exists so a parse that silently yields nothing cannot report
    'nothing is wired' with a straight face.
    """
    bodies: list[str] = []
    steps = 0
    for path in sorted(WORKFLOWS.glob("*.yml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            continue
        for job in (loaded.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if isinstance(step, dict) and isinstance(step.get("run"), str):
                    steps += 1
                    bodies.append(strip_comments(step["run"]))
    return "\n".join(bodies), steps


def self_test() -> int:
    """Three controls, each aimed at a way this checker could lie."""
    text, steps = run_bodies()
    failures: list[str] = []

    # 1. A name I have read a step for must read WIRED. Without this the
    #    parser could return nothing and every answer would be
    #    'unwired'.
    if "check-design-citations.py" not in text:
        failures.append("check-design-citations.py is wired but reads UNWIRED")

    # 2. A name that exists nowhere must read UNWIRED. A checker that
    #    finds everything is as useless as one that finds nothing.
    if "check-a-name-nobody-has-written.py" in text:
        failures.append("a fabricated name reads WIRED")

    # 3. The comment strip must actually strip. This is THE defect that
    #    produced two wrong censuses, so it gets a control of its own.
    if "zzz" in strip_comments("echo hi  # zzz\n"):
        failures.append("strip_comments left a commented name behind")

    # 4. THIS FILE MUST BE IN ITS OWN POPULATION, asserted rather than
    #    commented. The comment in `checkers()` claimed it already was,
    #    and the claim was INERT when I wrote it: `git ls-files` lists
    #    only TRACKED files, and the checker was still untracked, so it
    #    excluded itself for a reason the code never mentions. The
    #    census
    #    read 26 and silently became 27 on the commit that tracked it.
    #    A rename that stops matching the glob would do the same thing.
    me = pathlib.Path(__file__).name
    if me not in checkers():
        failures.append(f"{me} is NOT in its own population")

    print(f"run steps parsed: {steps}")
    for line in failures:
        print(f"  CONTROL FAILED: {line}")
    if failures:
        print(f"\n{len(failures)} control(s) failed. The instrument is wrong.")
        return 1
    print("4/4 controls passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="are the checkers wired?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    _reasons_are_non_empty()
    if args.self_test:
        return self_test()

    names = checkers()
    if not names:
        print("MATCHED ZERO checkers. An empty population reports full")
        print("coverage, which would mean nothing here. Exit 2.")
        return 2

    text, steps = run_bodies()
    if steps == 0:
        print("PARSED ZERO run steps out of the workflows. Every checker")
        print("would read as unwired for a reason that is not about the")
        print("checkers. This is a BROKEN INSTRUMENT. Exit 3.")
        return 3

    wired = [n for n in names if n in text]
    unwired = [n for n in names if n not in text]

    excused = [n for n in unwired if UNWIRED_BY_DECISION.get(n, "").strip()]
    unexplained = [n for n in unwired if n not in excused]
    stale = [n for n in UNWIRED_BY_DECISION if n in wired]
    unknown = [n for n in UNWIRED_BY_DECISION if n not in names]

    print(f"Checkers in docs/reviews/: {len(names)}")
    print(f"Run steps parsed from {WORKFLOWS.name}/: {steps}")
    print(f"WIRED: {len(wired)}")
    print(f"UNWIRED, with a stated reason: {len(excused)}")
    for name in excused:
        print(f"  EXEMPT   {name}: {UNWIRED_BY_DECISION[name]}")

    problems = False
    if unexplained:
        problems = True
        print(f"\n{len(unexplained)} checker(s) are UNWIRED and unexplained:")
        for name in unexplained:
            print(f"  {name}")
        print(
            "\nAn unwired checker is a claim of coverage nobody can see is\n"
            "false. Either wire it - after measuring it GREEN, because a\n"
            "gate that lands red is one people learn to ignore - or add it\n"
            "to UNWIRED_BY_DECISION with the reason."
        )

    if stale:
        problems = True
        print(f"\n{len(stale)} exemption(s) name a checker that IS wired:")
        for name in stale:
            print(f"  {name}")
        print("The reason has outlived the condition. Delete the entry.")

    bare = bare_python_steps(text)
    if bare:
        problems = True
        print(f"\n{len(bare)} checker(s) run by a BARE interpreter but need")
        print("more than the standard library:")
        for name, needed in bare:
            print(f"  {name}  needs {', '.join(needed)}")
        print(
            "\nA bare `python3` reaches only the standard library. The step\n"
            "passes wherever the module happens to be installed and dies\n"
            "with ModuleNotFoundError on a clean runner. Use\n"
            "`uv run --frozen python ...`, and declare the module in\n"
            "pyproject's dev group - a transitive dependency is a fact\n"
            "nobody promised you."
        )

    if unknown:
        problems = True
        print(f"\n{len(unknown)} exemption(s) name a file that does not exist:")
        for name in unknown:
            print(f"  {name}")
        print("A renamed or deleted checker leaves its exemption behind.")

    if problems:
        return 1

    print("\nEvery checker is wired, or unwired for a recorded reason.")
    print("NOTE: this proves each is INVOKED, not that its exit code gates")
    print("the job. A step that runs a checker and swallows its status")
    print("reads as WIRED here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
