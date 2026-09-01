#!/usr/bin/env python3
"""Prove `check-review-coverage.py`'s default ref survives a PR checkout.

    python3 docs/reviews/probe-coverage-ref-resolves.py

**THE DEFECT (R15-H1).** The checker defaulted `--ref` to `main`.
`actions/checkout` leaves a DETACHED HEAD and creates NO local `main`,
so on every pull request that ref does not resolve - and an
unresolvable ref reaches the `git()` guard, which exits **3**, the code
this project reserves for *"a BROKEN INSTRUMENT, not a finding"*.

**Wiring the gate with that default would have failed every PR with
"broken instrument" and taught nobody anything.** The docstring had said
`origin/main` since the file was written; only the default disagreed.
R12-H3 moved this off `HEAD` for the right reason and stopped one step
short.

**WHY A CONTROL AND NOT A COMMENT.** The defect is invisible in any
normal clone, because `git clone` CREATES a local `main`. My own first
attempt to reproduce it cloned and detached, found `main` resolving, and
briefly read the finding as wrong. The shape that matters is
`init` + `fetch` + `detach`, which is what the action actually leaves,
and no amount of prose keeps the next person from testing the easy shape
instead.

Exit 0 = the default ref resolves in a PR-shaped checkout and the
checker returns a VERDICT (0 or 1) rather than 3. Exit 1 = it does not.
Nothing outside a temporary directory is written or modified.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CHECKER = "docs/reviews/check-review-coverage.py"
BROKEN_INSTRUMENT = 3


def git(*args: str, cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """One git call, output captured, never raising on a bad status."""
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def pr_shaped_clone(into: pathlib.Path) -> pathlib.Path:
    """A checkout in the shape `actions/checkout` leaves on a PR.

    NOT `git clone`: that creates a local branch for the default
    branch, which is exactly what hides this defect. init + fetch +
    detach leaves the remote-tracking ref and no local branch at all.
    """
    work = into / "pr"
    work.mkdir()
    git("init", "-q", cwd=work)
    git("remote", "add", "origin", str(ROOT), cwd=work)
    # NOT --depth=1: CONTAINER_BASE needs real history, and a shallow
    # fetch would make this fail for a reason that has nothing to do
    # with ref resolution.
    git("fetch", "-q", "origin", "main", cwd=work)
    git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=work)
    return work


def main() -> int:
    """Run both arms and report."""
    results: list[tuple[bool, str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        work = pr_shaped_clone(pathlib.Path(tmp))

        local = git("rev-parse", "--verify", "-q", "main", cwd=work).returncode == 0
        remote = (
            git("rev-parse", "--verify", "-q", "origin/main", cwd=work).returncode == 0
        )
        results.append(
            (
                not local and remote,
                "SHAPE    ",
                f"a PR checkout has NO local main (local={local}) and"
                f" DOES have origin/main (remote={remote})",
            )
        )

        # RUN THE CLONE'S OWN COPY. My first version ran
        # `ROOT / CHECKER` with `cwd=work`, and that arm was VACUOUS:
        # the checker derives its repo from `__file__`, not from the
        # working directory, so it operated on the SOURCE tree where
        # `main` resolves perfectly. The amputation proved it - putting
        # the old `default="main"` back left the probe at 3/3. A control
        # that never runs its subject passes for free, which is the
        # defect this whole directory keeps re-finding.
        done = subprocess.run(
            [sys.executable, str(work / CHECKER)],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            (
                done.returncode != BROKEN_INSTRUMENT,
                "DEFAULT  ",
                f"the DEFAULT ref resolves there: exit {done.returncode}"
                f" (must not be {BROKEN_INSTRUMENT})",
            )
        )

        # POSITIVE CONTROL. A ref that genuinely cannot resolve MUST
        # still reach exit 3, or the arm above proves nothing: it would
        # pass just as well against a checker that never returns 3.
        done = subprocess.run(
            [sys.executable, str(work / CHECKER), "--ref", "no-such-ref-xyz"],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            (
                done.returncode == BROKEN_INSTRUMENT,
                "POSITIVE ",
                f"an unresolvable ref still exits {BROKEN_INSTRUMENT}"
                f" (got {done.returncode})",
            )
        )

        shutil.rmtree(work, ignore_errors=True)

    for ok, arm, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {arm} {detail}")
    passed = sum(1 for ok, _, _ in results if ok)
    print(f"\n{passed}/{len(results)} arms passed.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
