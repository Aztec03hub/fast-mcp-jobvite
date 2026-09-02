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

#: THE #147 MUTATION. `Committed file types, whole tree` is a multi-line
#: block, so before #147 `classify()` refused the whole step and the
#: probe never ran the invocation inside it. That is the step which
#: refused the tree for 127 commits. Making it FAIL and watching the
#: probe stay silent is the amputation: it puts the blindness back.
#:
#: An unknown flag rather than a real defect, because a control must not
#: need a broken tree to run. `check-committed-file-types.py` exits 2 on
#: an unrecognised argument (`main()`: `unknown = [a for a in argv[1:]
#: if a != "--all"]`), so the mutated line fails for a reason that is
#: entirely inside this control's own doing.
TREE_GOOD = "scripts/check-committed-file-types.py --all || {"
TREE_BAD = "scripts/check-committed-file-types.py --all --amputated || {"

#: The pre-#147 verdict for every multi-line block, restored by hand.
WAS = "multi-line block, has its own setup"

#: A tracked file this control OWNS, perturbed to make CI's whole-tree
#: form and the bare staged form DISAGREE. Its own source: no other
#: agent is editing it, and CPython has already read it in full by the
#: time this runs. `--all` reads WORKTREE blobs of TRACKED paths, the
#: bare form reads the STAGED set - so an unstaged NUL byte here is
#: refused by CI's form and invisible to the bare one. That is the
#: 127-commit shape, reproduced without touching anybody else's file
#: and without a commit.
SELF = pathlib.Path(__file__).resolve()
NUL = b"\x00 amputation marker, remove with: git checkout -- .\n"


def load() -> types.ModuleType:
    """A fresh import of the probe, so each arm starts unpatched."""
    spec = importlib.util.spec_from_file_location("probe_under_test", PROBE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {PROBE}. Exit 2.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_dirty(path: pathlib.Path) -> bool:
    """Whether git sees ANY uncommitted change to `path`."""
    done = subprocess.run(  # noqa: S603
        # fmt: off
        ["git", "-C", str(ROOT), "status", "--porcelain", "--", str(path)],  # noqa: S607
        # fmt: on
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(done.stdout.strip())


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
    return is_dirty(CI)


def mutate(frm: str, to: str) -> None:
    """Rewrite one unique line of `ci.yml`, or refuse."""
    text = CI.read_text(encoding="utf-8")
    count = text.count(frm)
    if count != 1:
        raise SystemExit(f"anchor occurs {count} times, expected 1: {frm!r}")
    CI.write_text(text.replace(frm, to), encoding="utf-8")


def arm(
    label: str,
    *,
    substitute: bool = True,
    blocks: bool = True,
    arguments: bool = True,
) -> tuple[int, bool, str]:
    """Run the probe once: `(exit code, traceback seen, output)`.

    Three independent amputations, because there are now three claims
    and each needs its own. `substitute` is #145's interpreter swap.
    `blocks` is #147's block reader - amputated, every multi-line step
    goes back to being refused unread, which is the selection bias
    itself. `arguments` is #147's bare-versus-flagged arm.

    Each `setattr` is guarded by a `hasattr` first. A control that
    amputates a name the subject no longer has amputates NOTHING and
    every arm passes; that is exactly how this file's first version was
    wrong, and the guard is cheaper than finding out again.
    """
    module = load()
    if not blocks:
        # AMPUTATION: restore the pre-#147 verdict - EVERY multi-line
        # block is refused unread, with the reason it used to carry.
        if not hasattr(module, "classify_block"):
            raise SystemExit(
                "the probe has no `classify_block`; this control would "
                "amputate nothing and every arm would pass. Exit 2."
            )
        setattr(module, "classify_block", lambda _: ("skip", WAS))  # noqa: B010
    if not arguments:
        # AMPUTATION: the bare-versus-flagged arm never runs.
        if not hasattr(module, "argument_arm"):
            raise SystemExit(
                "the probe has no `argument_arm`; this control would "
                "amputate nothing and every arm would pass. Exit 2."
            )
        setattr(module, "argument_arm", lambda: (0, []))  # noqa: B010
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
    print(f"  block reader        : {'ACTIVE' if blocks else 'AMPUTATED'}")
    print(f"  argument arm        : {'ACTIVE' if arguments else 'AMPUTATED'}")
    print(f"  probe exit          : {code}")
    print(f"  real MNFE traceback : {traceback_seen}")
    for line in text.splitlines():
        if line.startswith("Ran ") or "EXIT=" in line or "DISAGREE" in line:
            print(f"  {line.strip()}")
    return code, traceback_seen, text


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
        code, seen, _ = arm("A. clean ci.yml, swap ACTIVE", substitute=True)
        if code != 0 or seen:
            failures.append("A: a clean tree must be green with no traceback")

        mutate(GOOD, BAD)
        if not ci_is_dirty():
            print("The mutation did NOT land; git reports no diff. Exit 2.")
            return 2

        code, seen, _ = arm("C1. MUTATED, swap ACTIVE", substitute=True)
        if code != 1 or not seen:
            failures.append(
                "C1: the probe must go red on a REAL ModuleNotFoundError. "
                "This is the whole claim; without it the probe is still "
                "borrowing its red from the static checker."
            )

        code, seen, _ = arm("C2. MUTATED, swap AMPUTATED", substitute=False)
        if code != 1 or seen:
            failures.append(
                "C2: without the swap the probe must still go red, but "
                "with NO traceback - that is the borrowed detection R13 "
                "found. A traceback here means the amputation did not "
                "take, and C1 proves nothing."
            )

        mutate(BAD, GOOD)
        mutate(TREE_GOOD, TREE_BAD)
        if not ci_is_dirty():
            print("The #147 mutation did NOT land; git reports no diff. Exit 2.")
            return 2

        # THE ARGUMENT ARM IS AMPUTATED IN BOTH E ARMS, and it had to
        # be.
        # The first version of E left it running, and E2 - the arm that
        # must be GREEN with the block reader amputated - came back RED.
        # The mutated line still carries `--all`, so the argument arm
        # caught the disagreement on its own and supplied a red that had
        # nothing to do with reading blocks. That is the borrowed-red
        # failure this file was written about, rebuilt one mechanism
        # over, and it took this control to see it.
        code, _, _ = arm("E1. whole-tree step BROKEN, blocks ACTIVE", arguments=False)
        if code != 1:
            failures.append(
                "E1: the probe must go red when `Committed file types, "
                "whole tree` fails. It is a multi-line block, and before "
                "#147 that meant the invocation inside it was never run."
            )

        code, _, _ = arm(
            "E2. whole-tree step BROKEN, blocks AMPUTATED",
            blocks=False,
            arguments=False,
        )
        if code != 0:
            failures.append(
                "E2: with the block reader amputated the probe must be "
                "GREEN over a broken step - that is the selection bias "
                "itself, and if this arm goes red the bias was never "
                "what E1 is claiming to have fixed."
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
        text = CI.read_text(encoding="utf-8")
        if BAD in text:
            mutate(BAD, GOOD)
        if TREE_BAD in text:
            mutate(TREE_BAD, TREE_GOOD)

    if ci_is_dirty():
        print("\nRESTORE FAILED: ci.yml is still dirty. Fix it by hand")
        print("before doing anything else. Exit 3.")
        return 3

    code, seen, _ = arm("D. restored, swap ACTIVE", substitute=True)
    if code != 0 or seen:
        failures.append("D: the restored tree must be green again")

    print("\nci.yml restored; git reports no diff for it.")

    # ARMS F: THE ARGUMENT ARM, ON A TREE WHERE THE TWO FORMS DISAGREE.
    # `--all` reads WORKTREE blobs of TRACKED paths; the bare form reads
    # the STAGED set. So an unstaged NUL byte in a tracked file is
    # refused by CI's form and INVISIBLE to the bare one - the exact
    # shape that hid a red trunk for 127 commits, reproduced without a
    # commit and without touching a file another agent might hold.
    # THE GUARD HERE IS BYTES, NOT `git status`, AND THE DIFFERENCE
    # MATTERS. `ci_is_dirty()` is right for `ci.yml`: that mutation is a
    # string replace against a file this control does not own, so git is
    # the only honest witness that it landed and was undone. This one is
    # different - the exact prior bytes are held in memory and written
    # back, so restoration is provable directly and more strongly than
    # git can. Using git here as well would have been the tidy-looking
    # choice and would have made the control unrunnable on any tree
    # where this file is edited, which is every tree where it is being
    # worked on. Measured: the first version refused to run for exactly
    # that reason.
    print(f"\nPERTURBING {SELF.name} with a NUL byte. If this process is")
    print("KILLED the file is left holding it. Recover with:")
    print(f"    git -C {ROOT} checkout -- {SELF}")
    original = SELF.read_bytes()
    try:
        SELF.write_bytes(original + NUL)
        if SELF.read_bytes() == original:
            print("The perturbation did NOT land; the bytes are unchanged.")
            print("Exit 2.")
            return 2

        # THE BLOCK READER IS AMPUTATED IN BOTH F ARMS, and it took a
        # failing arm to work out why. With it ACTIVE the probe RUNS
        # `check-committed-file-types.py --all` as a step, that step
        # goes red on the perturbed tree, and F2 - which must be green -
        # came back red. Both mechanisms fire on this instance, so with
        # blocks active F1 proves nothing about the ARM.
        #
        # Amputating blocks is not a dodge, it is the question. Before
        # #147 no probe ran that step at all, and the claim being tested
        # is that THE ARM ALONE would have caught the 127-commit red.
        # These two arms are that world: F2 is what the probe did on the
        # night it was blind, F1 is the same tree with only the arm
        # added. The arm's other value - checkers whose step is STILL
        # not run, and silent disagreements where both forms exit 0 -
        # is not covered by any arm here and is not claimed.
        code, _, text = arm("F1. tree perturbed, arm ACTIVE, blocks OFF", blocks=False)
        if code != 1 or "DISAGREE" not in text:
            failures.append(
                "F1: CI's `--all` form must refuse this file while the "
                "bare form examines the empty staged set and exits 0. "
                "The arm must SAY they disagree and the probe must go red."
            )

        code, _, text = arm(
            "F2. tree perturbed, arm OFF, blocks OFF",
            arguments=False,
            blocks=False,
        )
        if code != 0 or "DISAGREE" in text:
            failures.append(
                "F2: with BOTH the arm and the block reader amputated "
                "the probe must be GREEN on the same perturbed tree. That "
                "green is the pre-#147 blindness itself. If it goes red, "
                "F1's red was supplied by something else and proves "
                "nothing - precisely how C1's predecessor was wrong."
            )
    finally:
        SELF.write_bytes(original)

    if SELF.read_bytes() != original:
        print(f"\nRESTORE FAILED: {SELF.name} does not match the bytes read")
        print("before the perturbation. Fix it by hand before doing")
        print("anything else. Exit 3.")
        return 3
    print(f"{SELF.name} restored; its bytes match what was read.")

    for line in failures:
        print(f"  ARM FAILED: {line}")
    if failures:
        print(f"\n{len(failures)} of 8 arms failed. The probe's claim is not")
        print("supported by this control.")
        return 1
    print("8/8 arms as expected. C1 red on its OWN traceback, C2 red")
    print("without one: the probe detects a bare interpreter itself.")
    print("E1 red on a broken multi-line step, E2 GREEN on the same step")
    print("with the block reader amputated: that green IS the selection")
    print("bias #147 fixed, measured rather than argued. F1 red on the")
    print("argument arm ALONE with the block reader off, F2 green with")
    print("both off: the arm by itself would have caught the whole-tree")
    print("gate that a bare local run reported clean for 127 commits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
