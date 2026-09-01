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

**WHY THE JSON BRANCH EXISTS, CORRECTED** (R14-R1 H1). The first
version of this paragraph said a widened line rule "reports a clean
zero whatever the manifest said". **That is false on today's tree**,
and an amputation deleting the whole JSON branch exits 0 - a SURVIVOR.
The reason is the wording this round itself chose: `server.json`'s
description BEGINS with the variable name, so name and marker share a
line and the plain rule matches.

**What the branch actually prevents is a FALSE POSITIVE.** A
description that carries the marker WITHOUT repeating the variable name
is a correctly marked manifest that the line rule calls unmarked,
failing the gate on a manifest that is telling the truth. The
LINE-RULE arm below measures exactly that, and it is what makes the
branch load-bearing rather than decorative. A checker must not depend
on how one description happens to be phrased.

Every arm mutates the working tree and restores it. The tree is
compared against `git` at the end and a mismatch is a FAILURE, not a
warning: a probe that leaves its mutation behind makes the next reader
measure the probe.
"""

from __future__ import annotations

import json
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
#: The marker text itself, for building plants.
UNMARKED_KEY = "NOT YET IMPLEMENTED"

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


VARIABLE = "JOBVITE_OUTBOUND_RATE_LIMIT"


def read_manifest() -> dict:
    """The manifest, parsed."""
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def write_manifest(document: dict) -> None:
    """Write a parsed manifest back, formatting irrelevant to the check."""
    MANIFEST.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def rate_limit_entry(document: dict) -> dict:
    """The one real declaration, or refuse - a plant needs a subject."""
    for package in document.get("packages", []):
        for entry in package.get("environmentVariables", []):
            if entry.get("name") == VARIABLE:
                return entry
    message = f"{MANIFEST.name} has no {VARIABLE} entry to plant against"
    raise SystemExit(message)


def plant_duplicate(document: dict) -> dict:
    """A SECOND declaration of the same name, deliberately unmarked."""
    clone = dict(rate_limit_entry(document))
    clone["description"] = "An outbound self-throttle, requests per minute."
    document["packages"][0]["environmentVariables"].append(clone)
    return document


def plant_outside(document: dict) -> dict:
    """Strip the real entry; plant a MARKED look-alike out of scope."""
    for package in document.get("packages", []):
        package["environmentVariables"] = [
            entry
            for entry in package.get("environmentVariables", [])
            if entry.get("name") != VARIABLE
        ]
    document["decoy"] = {"name": VARIABLE, "description": f"{VARIABLE} {UNMARKED_KEY}"}
    return document


def tree_is_clean() -> bool:
    """Do `server.json` and the checker match what git has?"""
    done = subprocess.run(
        # HEAD, not the index. `git diff --quiet` alone compares the
        # worktree to the INDEX, so a modified-and-staged file reads
        # CLEAN - and this guard's own message says "commit or stash
        # first". Measured: modify+`git add` gives exit 0 without HEAD
        # and exit 1 with it (R14-R1 N1).
        ["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--",
         str(MANIFEST), str(CHECKER)],
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

        # LINE-RULE: THE ARM THAT MAKES THE JSON BRANCH LOAD-BEARING
        # (R14-R1 H1). Reword the description so it carries the marker
        # WITHOUT repeating the variable name. That is a CORRECTLY
        # marked manifest. The structural reader must accept it; a
        # line rule cannot, because name and marker no longer share a
        # line. Without this arm the whole branch is an amputation
        # survivor - deleting it changes nothing, because every
        # description here happens to begin with its own variable name.
        prose = "Not implemented yet. NOT YET IMPLEMENTED: no code reads it."
        substitute(MANIFEST, PUBLISHED, prose)
        code, out = run_checker()
        results.append(
            (
                code == 0,
                "LINE-RULE",
                f"a marker WITHOUT the variable name beside it is still"
                f" accepted (exit {code}) - the line rule would refuse this",
            )
        )
        substitute(MANIFEST, prose, PUBLISHED)

        # SCOPE-DUP: a DUPLICATE entry, one marked and one not, must be
        # refused rather than laundered (R14-R1 H2). Built by editing
        # the PARSED document, not by string substitution: these plants
        # are about JSON STRUCTURE, and a textual edit could not place
        # a node outside `environmentVariables` at all.
        write_manifest(plant_duplicate(read_manifest()))
        code, out = run_checker()
        results.append(
            (
                code != 0 and "2 times" in out,
                "SCOPE-DUP",
                f"a DUPLICATE declaration is refused, not laundered (exit {code})",
            )
        )

        # SCOPE-OUT: strip the real entry and plant a MARKED look-alike
        # OUTSIDE packages[*].environmentVariables. The old whole-document
        # walk accepted this and exited 0 on a manifest with no real
        # declaration at all (R14-R1 H2, second plant).
        write_manifest(plant_outside(read_manifest()))
        code, out = run_checker()
        results.append(
            (
                code != 0 and "declares no" in out,
                "SCOPE-OUT",
                f"a look-alike outside environmentVariables does not count"
                f" (exit {code})",
            )
        )
        subprocess.run(
            ["git", "-C", str(ROOT), "checkout", "--", str(MANIFEST)], check=False
        )

        # VACUITY: a manifest whose entry is missing must RAISE, not
        # report a clean zero. A checker that cannot find its subject
        # and says nothing is the failure this whole file exists for.
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
        # No manual restore here: the `finally` reverts to git, and the
        # snapshot this used to take was captured AFTER the POSITIVE arm
        # had already unmarked the manifest, so it restored the WRONG
        # state and only looked like the restore (R14-R1 N2).
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
