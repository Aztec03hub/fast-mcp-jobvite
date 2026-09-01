#!/usr/bin/env python3
"""Prove `check-settings-are-read.py` now sees the PUBLISHED manifest.

    python3 docs/reviews/probe-r14-manifest-marker.py

**THE DEFECT THIS GUARDS (R14-H1).** `check-settings-are-read.py` grew
an arm requiring that a declared-but-unread setting be marked
`NOT YET IMPLEMENTED` in the artefacts an operator reads. Its own
docstring argues the arm into existence and ends by naming the harm:
*"and `server.json` advertises it to registry consumers as a knob that
works"*. The enforced tuple then held `README.md` and `.env.example`
and stopped. **The artefact the paragraph names is the one the check
omitted**, and it is the only one of the three that leaves this
repository - the other two are read by someone who has already cloned
us.

**WHY A LINE RULE COULD NOT HAVE BEEN JUST WIDENED.** The text arm
requires the variable name and the marker on ONE line. A JSON object
puts `"name"` and `"description"` on different lines by construction,
so adding `server.json` to the tuple alone would have produced a check
that reports a clean zero whatever the manifest said - a third arm that
passes by never being able to match. That is why the AMPUTATE arm below
is the load-bearing one: it restores the two-artefact tuple and shows
the old checker exits 0 on a manifest that lies.

Every arm mutates the working tree and restores it. The tree is
compared against `git` at the end and a mismatch is a FAILURE, not a
warning: a probe that leaves its mutation behind makes the next reader
measure the probe.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CHECKER = ROOT / "docs" / "reviews" / "check-settings-are-read.py"
MANIFEST = ROOT / "server.json"

#: The marker text as it stands in the manifest description today.
PUBLISHED = (
    "JOBVITE_OUTBOUND_RATE_LIMIT IS NOT YET IMPLEMENTED (ADR-0025): it is "
    "declared and validated, and no code reads it, so setting it changes "
    "nothing today. Intended as an outbound"
)
#: What it said before R14-H1, and what a regression would restore.
UNMARKED = "An outbound"

#: The three-artefact tuple, and the two-artefact one it replaced.
WIDE = '("README.md", ".env.example", "server.json"),'
NARROW = '("README.md", ".env.example"),'


def run_checker() -> tuple[int, str]:
    """The checker's exit code and combined output."""
    done = subprocess.run(
        [sys.executable, str(CHECKER)],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode, done.stdout + done.stderr


def substitute(path: pathlib.Path, old: str, new: str) -> None:
    """Replace `old` with `new`, unless it appears other than once.

    An anchor that matches twice would edit a site this probe never
    reasoned about; an anchor that matches zero times would make the arm
    measure an unmutated tree and report a pass. Both are the same
    class of silent wrong answer, so both raise.
    """
    body = path.read_text(encoding="utf-8")
    if body.count(old) != 1:
        message = f"{path.name}: anchor appears {body.count(old)} times, need 1"
        raise SystemExit(message)
    path.write_text(body.replace(old, new), encoding="utf-8")


def tree_is_clean() -> bool:
    """Do `server.json` and the checker match what git has?"""
    done = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--quiet", "--", str(MANIFEST), str(CHECKER)],
        check=False,
    )
    return done.returncode == 0


def main() -> int:
    """Run the arms, restore the tree, and report."""
    if not tree_is_clean():
        print("REFUSING: server.json or the checker is already modified.")
        print("This probe restores by reverting to git, which would DESTROY")
        print("uncommitted work. Commit or stash first.")
        return 2

    results: list[tuple[bool, str, str]] = []
    try:
        code, _ = run_checker()
        results.append(
            (code == 0, "BASELINE ", f"the tree as committed passes (exit {code})")
        )

        # POSITIVE: strip the marker from the manifest only.
        substitute(MANIFEST, PUBLISHED, UNMARKED)
        code, out = run_checker()
        named = "server.json" in out
        results.append(
            (
                code == 1 and named,
                "POSITIVE ",
                f"an unmarked manifest is REFUSED (exit {code}, names it: {named})",
            )
        )

        # AMPUTATE: with the manifest still unmarked, restore the old
        # two-artefact tuple. The old checker must go GREEN on the lie.
        substitute(CHECKER, WIDE, NARROW)
        code, _ = run_checker()
        results.append(
            (
                code == 0,
                "AMPUTATE ",
                f"the OLD two-artefact tuple passes on the same lie (exit {code})"
                " - this is the defect, reproduced",
            )
        )
        substitute(CHECKER, NARROW, WIDE)

        # VACUITY: a manifest whose entry is missing must RAISE, not
        # report a clean zero. A checker that cannot find its subject
        # and says nothing is the failure this whole file exists for.
        body = MANIFEST.read_text(encoding="utf-8")
        substitute(MANIFEST, '"JOBVITE_OUTBOUND_RATE_LIMIT"', '"JOBVITE_GONE"')
        code, out = run_checker()
        results.append(
            (
                code != 0 and "declares no" in out,
                "VACUITY  ",
                f"a manifest with no such entry REFUSES rather than passing"
                f" (exit {code})",
            )
        )
        MANIFEST.write_text(body, encoding="utf-8")
    finally:
        subprocess.run(
            ["git", "-C", str(ROOT), "checkout", "--", str(MANIFEST), str(CHECKER)],
            check=False,
        )

    for ok, arm, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {arm} {detail}")

    if not tree_is_clean():
        print("\nFAIL: the tree did NOT come back clean. A later reader would")
        print("measure this probe's leftovers instead of the repository.")
        return 1

    passed = sum(1 for ok, _, _ in results if ok)
    print(f"\n{passed}/{len(results)} arms passed, tree restored.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
