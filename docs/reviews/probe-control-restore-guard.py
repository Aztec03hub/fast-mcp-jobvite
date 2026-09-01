#!/usr/bin/env python3
"""Does the ci.yml control's `finally` destroy its own diagnosis?

`probe-ci-checker-steps-control.py` runs arm A INSIDE its `try`, before
the mutation. An unconditional `mutate(BAD, GOOD)` in the `finally`
therefore runs against a CLEAN file whenever arm A raises, finds the BAD
anchor zero times, and raises `anchor occurs 0 times, expected 1`. The
operator reads that as "the workflow is damaged" while the tree is
pristine, and the ACTUAL failure - whatever arm A hit - is gone.

**BOTH DIRECTIONS ARE MEASURED HERE**, because a fix asserted only on
the after-state cannot tell a working guard from a control that never
reproduced the defect. The BEFORE arm loads the pre-fix source out of
git and must show the masking; the AFTER arm loads the working tree and
must show the original exception escaping intact.

NOTHING IS KILLED AND THE REAL WORKFLOW IS NEVER TOUCHED. `CI` is
repointed at a temporary copy and `ci_is_dirty` is stubbed, so the
subject's own git calls never run. The tree is asserted clean at exit.

Run with `uv run --frozen python` on
`docs/reviews/probe-control-restore-guard.py`.
"""

from __future__ import annotations

import contextlib
import io
import pathlib
import subprocess
import sys
import tempfile
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SUBJECT = ROOT / "docs" / "reviews" / "probe-ci-checker-steps-control.py"
REAL_CI = ROOT / ".github" / "workflows" / "ci.yml"

#: What arm A raises in this experiment. It has to be a message no
#: other failure could produce, or "the diagnosis survived" would be
#: unfalsifiable.
NEEDLE = "ARM A BLEW UP (simulated import error)"

#: The message the unguarded `finally` produces instead.
MASK = "anchor occurs 0 times"


def load(source: str, name: str) -> types.ModuleType:
    """Load a version of the subject from SOURCE TEXT, not from disk.

    The BEFORE arm's text comes out of git, so it must be importable
    without ever being written into the working tree.
    """
    module = types.ModuleType(name)
    module.__file__ = str(SUBJECT)
    exec(compile(source, str(SUBJECT), "exec"), module.__dict__)  # noqa: S102
    return module


def before_text() -> str:
    """The subject as it stood on `origin/main`, from git objects."""
    rel = SUBJECT.relative_to(ROOT)
    done = subprocess.run(  # noqa: S603
        ["git", "-C", str(ROOT), "show", f"origin/main:{rel}"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout


def run_arm(label: str, source: str, name: str) -> str:
    """Make arm A raise, run `main()`, and return what escaped."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = pathlib.Path(tmp) / "ci.yml"
        copy.write_text(REAL_CI.read_text(encoding="utf-8"), encoding="utf-8")

        module = load(source, name)
        module.CI = copy  # type: ignore[attr-defined]
        module.ci_is_dirty = lambda: False  # type: ignore[attr-defined]

        def raiser(*_args: object, **_kwargs: object) -> tuple[int, bool]:
            raise RuntimeError(NEEDLE)

        module.arm = raiser  # type: ignore[attr-defined]

        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                module.main()
        except BaseException as exc:  # noqa: BLE001
            escaped = f"{type(exc).__name__}: {exc}"
        else:
            escaped = "NOTHING - main() returned normally"

        clean = copy.read_text(encoding="utf-8") == REAL_CI.read_text(encoding="utf-8")
        print(f"\n=== {label} ===")
        print(f"  escaped exception : {escaped}")
        print(f"  copy still clean  : {clean}")
        return escaped


def main() -> int:
    """BEFORE must mask, AFTER must not. Anything else fails."""
    failures: list[str] = []

    before = run_arm("BEFORE (origin/main)", before_text(), "control_before")
    if MASK not in before:
        failures.append(
            "BEFORE did not reproduce the masking. Either origin/main "
            "already carries the fix or this probe is not exercising "
            "the `finally` - either way the AFTER arm proves nothing."
        )
    if NEEDLE in before:
        failures.append("BEFORE kept the real diagnosis; nothing to fix")

    after_text = SUBJECT.read_text(encoding="utf-8")
    after = run_arm("AFTER (working tree)", after_text, "control_after")
    if NEEDLE not in after:
        failures.append(f"AFTER lost the real diagnosis: {after}")
    if MASK in after:
        failures.append("AFTER still masks with the anchor message")

    # The real workflow was never a subject here; prove it.
    done = subprocess.run(  # noqa: S603
        # fmt: off
        ["git", "-C", str(ROOT), "status", "--porcelain", "--", str(REAL_CI)],  # noqa: S607
        # fmt: on
        capture_output=True,
        text=True,
        check=True,
    )
    if done.stdout.strip():
        failures.append(f"the REAL ci.yml is dirty: {done.stdout.strip()!r}")

    print(f"\narms=2 failures={len(failures)}")
    for line in failures:
        print(f"  {line}")
    if failures:
        return 1
    print("The guard reproduces the defect and removes it. Real ci.yml clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
