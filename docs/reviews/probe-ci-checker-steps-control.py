#!/usr/bin/env python3
"""Prove the probe can detect a bare interpreter on its own.

    uv run --frozen python \
        docs/reviews/probe-ci-checker-steps-control.py

**WHY THIS EXISTS.** Review R13 measured that the probe's founding
control passed for another gate's reason. R13 mutated `ci.yml` to
`python3 docs/reviews/check-checkers-are-wired.py` and the probe went
red - but only because that checker is itself one of the commands the
probe runs, and it caught the bad YAML *statically*. No
`ModuleNotFoundError` occurred and none could: the probe ran the
checker with the local `python3`, which has pyyaml. **A green, or a
red, supplied by a different gate is not this gate working.**

`probe-*`, not `check-*`, for the reason its subject records: a
`check-*` here would have to be wired into CI, and this one MUTATES
`ci.yml`. It must never share a job with its subject.

## The first version of this control was wrong, and how

R13 said "take that one checker out of the runnable set and the probe
is blind", so the obvious control removes it and mutates anyway. It
stays green - which reads as confirmation and is worthless. **The
checker being removed and the step being mutated are THE SAME STEP**,
the single line `run: ... check-checkers-are-wired.py`. Removing it
removes the subject of the mutation, so that arm cannot go red for any
reason whatever, and an arm that cannot fail measures nothing.

What actually separates the two mechanisms is not which step runs but
which INTERPRETER runs it, so that is what this amputates:

  C1  swap ACTIVE     the isolated interpreter has no pyyaml, so the
                      checker dies at import - the probe's OWN
                      detection, evidenced by a real traceback
  C2  swap AMPUTATED  the local python3 has pyyaml, so the checker
                      RUNS and detects the mutated YAML statically -
                      red, but borrowed, and no traceback anywhere

Same mutation, same runnable set, one exit code, two different
reasons for it. C2 is the behaviour R13 found; C1 is what was added.

**AND THE FIRST NEEDLE HERE WAS ALSO WRONG.** Searching the output for
the word `ModuleNotFoundError` reported C2 as a real traceback, because
`check-checkers-are-wired.py`'s own advice text contains that word -
the grep found the DOCUMENTATION of the defect and scored it as the
defect. The needle is the exception's real form, which carries a
module name that the prose does not.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import shlex
import subprocess
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CI = ROOT / ".github" / "workflows" / "ci.yml"
PROBE = ROOT / "docs" / "reviews" / "probe-ci-checker-steps.py"

GOOD = "run: uv run --frozen python docs/reviews/check-checkers-are-wired.py"
BAD = "run: python3 docs/reviews/check-checkers-are-wired.py"

#: The exception's REAL form. The bare word appears in the subject's
#: own prose; this does not.
NEEDLE = "ModuleNotFoundError: No module named"


def load() -> types.ModuleType:
    """A fresh import of the probe, so each arm starts unpatched."""
    spec = importlib.util.spec_from_file_location("probe_under_test", PROBE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {PROBE}. Exit 2.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ci_is_dirty() -> bool:
    """Whether git sees a diff in `ci.yml`.

    Against git, never against a string compare: a `replace` that
    matched nothing succeeds silently, and the arm then passes for a
    reason unrelated to the code.
    """
    done = subprocess.run(  # noqa: S603
        ["git", "-C", str(ROOT), "diff", "--name-only", "--", str(CI)],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(done.stdout.strip())


def mutate(frm: str, to: str) -> None:
    """Rewrite one unique line of `ci.yml`, or refuse."""
    text = CI.read_text(encoding="utf-8")
    count = text.count(frm)
    if count != 1:
        raise SystemExit(f"anchor occurs {count} times, expected 1: {frm!r}")
    CI.write_text(text.replace(frm, to), encoding="utf-8")


def arm(label: str, *, substitute: bool) -> tuple[int, bool]:
    """Run the probe once, returning `(exit code, traceback seen)`."""
    module = load()
    if not substitute:
        # AMPUTATION: every command runs under the interpreter the
        # workflow names, found on PATH - the behaviour before #145.
        # `setattr` because mypy types a dynamically loaded module as
        # having no attributes; the name is checked below rather than
        # assumed, so a rename cannot leave this silently amputating
        # nothing.
        if not hasattr(module, "resolve_argv"):
            raise SystemExit(
                "the probe has no `resolve_argv`; this control would "
                "amputate nothing and every arm would pass. Exit 2."
            )
        setattr(module, "resolve_argv", shlex.split)  # noqa: B010

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = int(module.main())
    text = buffer.getvalue()
    traceback_seen = NEEDLE in text

    print(f"\n=== {label} ===")
    print(f"  ci.yml mutated      : {ci_is_dirty()}")
    print(f"  interpreter swap    : {'ACTIVE' if substitute else 'AMPUTATED'}")
    print(f"  probe exit          : {code}")
    print(f"  real MNFE traceback : {traceback_seen}")
    for line in text.splitlines():
        if line.startswith("Ran ") or "EXIT=" in line:
            print(f"  {line.strip()}")
    return code, traceback_seen


def main() -> int:
    """Four arms, and the tree restored whatever happens."""
    if ci_is_dirty():
        print("ci.yml already has uncommitted changes. Refusing to mutate")
        print("on top of them - the restore would not be provable. Exit 2.")
        return 2

    failures: list[str] = []
    try:
        code, seen = arm("A. clean ci.yml, swap ACTIVE", substitute=True)
        if code != 0 or seen:
            failures.append("A: a clean tree must be green with no traceback")

        mutate(GOOD, BAD)
        if not ci_is_dirty():
            print("The mutation did NOT land; git reports no diff. Exit 2.")
            return 2

        code, seen = arm("C1. MUTATED, swap ACTIVE", substitute=True)
        if code != 1 or not seen:
            failures.append(
                "C1: the probe must go red on a REAL ModuleNotFoundError. "
                "This is the whole claim; without it the probe is still "
                "borrowing its red from the static checker."
            )

        code, seen = arm("C2. MUTATED, swap AMPUTATED", substitute=False)
        if code != 1 or seen:
            failures.append(
                "C2: without the swap the probe must still go red, but "
                "with NO traceback - that is the borrowed detection R13 "
                "found. A traceback here means the amputation did not "
                "take, and C1 proves nothing."
            )
    finally:
        mutate(BAD, GOOD)

    if ci_is_dirty():
        print("\nRESTORE FAILED: ci.yml is still dirty. Fix it by hand")
        print("before doing anything else. Exit 3.")
        return 3

    code, seen = arm("D. restored, swap ACTIVE", substitute=True)
    if code != 0 or seen:
        failures.append("D: the restored tree must be green again")

    print("\nci.yml restored; git reports no diff for it.")
    for line in failures:
        print(f"  ARM FAILED: {line}")
    if failures:
        print(f"\n{len(failures)} of 4 arms failed. The probe's claim is not")
        print("supported by this control.")
        return 1
    print("4/4 arms as expected: C1 red on its OWN traceback, C2 red")
    print("without one. The probe detects a bare interpreter itself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
