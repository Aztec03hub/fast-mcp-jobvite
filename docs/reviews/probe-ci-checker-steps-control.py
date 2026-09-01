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
    """Whether git sees ANY uncommitted change to `ci.yml`.

    Against git, never against a string compare: a `replace` that
    matched nothing succeeds silently, and the arm then passes for a
    reason unrelated to the code.

    **`git status --porcelain`, NOT `git diff`.** `git diff` compares
    the worktree to the INDEX, so a `ci.yml` that was edited and then
    `git add`-ed reads CLEAN - and the pre-flight guard below, whose
    whole job is to refuse to measure on top of somebody's edit, would
    wave it through. Measured: modify + `git add` gives `git diff
    --quiet` exit 0 and `git status --porcelain` a non-empty `M `.

    `--porcelain` covers staged, unstaged and untracked in one call,
    which is why it beats `git diff --quiet HEAD` here. This is the
    SECOND instance of the `git diff` mistake in this directory; the
    first was `probe-r14-manifest-marker.py`.

    One predicate serves three questions - is the tree clean before we
    start, did the mutation land, is it restored - and that is sound
    only because the first question is asked FIRST and returns False.
    Once `ci.yml` matches HEAD, index and worktree agree, so all three
    readings coincide.
    """
    done = subprocess.run(  # noqa: S603
        # fmt: off
        ["git", "-C", str(ROOT), "status", "--porcelain", "--", str(CI)],  # noqa: S607
        # fmt: on
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

    # SAY HOW TO RECOVER BEFORE THERE IS ANYTHING TO RECOVER FROM.
    # `finally` covers an exception and SIGINT. It does NOT cover
    # SIGTERM, SIGKILL, or the process being reaped with its worktree -
    # and what those leave on disk is a `ci.yml` holding the BAD line,
    # looking like an ordinary edit. That is the exact shape that kept
    # the trunk red for 127 commits. Printed FIRST because a message
    # written after the mutation is a message the kill never reaches.
    print("MUTATING ci.yml. If this process is KILLED (SIGTERM/SIGKILL,")
    print("or the worktree is removed under it) the tree is left holding")
    print("the BAD line and nothing will say so. Recover with:")
    # `CI` verbatim, NOT `CI.relative_to(ROOT)`: `relative_to` RAISES
    # when the two are unrelated, so the warning about a killed process
    # would itself crash the process. Found by
    # `probe-control-restore-guard.py`, which repoints `CI` at a copy -
    # the recovery notice was the first thing to blow up.
    print(f"    git -C {ROOT} checkout -- {CI}")
    print()

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
        # RESTORE ONLY WHAT ACTUALLY LANDED. Arm A runs inside this
        # `try`, BEFORE the mutation. If arm A raises - or if
        # `mutate(GOOD, BAD)` itself refuses because someone reflowed
        # the workflow - an unconditional `mutate(BAD, GOOD)` runs
        # against a CLEAN file, finds the BAD anchor zero times, and
        # raises `anchor occurs 0 times`. The operator is then told the
        # tree is damaged, which it is not, and the real diagnosis is
        # gone: the cleanup destroys the failure it was meant to
        # survive. Reproduced by pointing `CI` at a copy and making arm
        # A raise; no kill and no touch of the real workflow.
        if BAD in CI.read_text(encoding="utf-8"):
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
