#!/usr/bin/env python3
"""Report the commits on `main` that NO review round has ever covered.

    python3 docs/reviews/check-review-coverage.py

**WHY THIS EXISTS.** On 2026-09-01 I found 45 consecutive commits that
no review round had examined - 133 files, +7787/-2561 - including nine
ADRs applied to the frozen design, a tenth applied after it, the sweep
that took `docs/` off the ruff and mypy exclusions, and the fixes an
earlier round had itself demanded. I found them by accident, while
checking whether a filename collided.

**IT WAS NOT AN OVERSIGHT, IT WAS THE MODEL.** Every round through R8
reviewed a UNIT - `REVIEW-R4` says *"U5, search_jobs"*, `REVIEW-R6`
says *"U7, resilience"*. R9 was the first to review a RANGE. So fixes,
chores, checkers, CI and ADR application were never in any round's
scope by construction. Measured over those 45 commits: a grep for
`feat/u<n>` or a bare `U<n>` matches **zero** of them, and all 18
merges in the range are `fix/*` or `chore/*`.

**And they are the instruments.** The least-reviewed code in this
repository is the code that does the reviewing - the checkers whose
greens license every other claim made here.

**WHY THIS CHECKER REFUSES TO GUESS.** That is its main design
decision. The obvious implementation derives each round's coverage
from the SHA its document cites. It is not sound: of the seven
code-review documents, only ONE cites a range (`CODE-REVIEW-R9`,
*"between 8695101 (exclusive) and f699f74"*). The rest cite the SHA
they reviewed AT - the merged tree state - and all but one of those
are plain commits, not merges, so there is no `M^1..M` to expand.

A checker that inferred a range from those would **manufacture
coverage for code nobody read**, and certify it forever. That is
strictly worse than the gap it closes: an absence you can see beats a
false presence you cannot. So coverage must be DECLARED, and a
document with no declaration is reported as UNDECLARED, never guessed.

**WHAT IT CANNOT DO.** It checks that a commit falls inside some
round's declared range. It cannot check that the round actually READ
that commit, or read it carefully. A declaration is a claim by its
author; this gate only makes the claim explicit and total. That is the
same "resolves is not correct" limit the citation checkers carry, said
out loud rather than discovered later.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
REVIEWS = ROOT / "docs" / "reviews"

#: The machine-readable declaration a review document must carry. It is
#: an HTML comment, so it renders as nothing in the document itself.
DECLARATION = re.compile(
    r"^<!--\s*REVIEW-COVERS:\s*"
    r"(?P<base>[0-9a-f]{7,40})\.\.(?P<head>[0-9a-f]{7,40})\s*-->\s*$",
    re.MULTILINE,
)

#: Documents that predate the declaration and cannot be given one
#: HONESTLY, each with the reason. These reviewed a UNIT, not a range,
#: and the SHA each cites is the tree it read at - not a range
#: boundary. Inventing ranges for them is the one thing this checker
#: must never do.
#:
#: A bare name is refused: the reason IS the exemption. Clearing an
#: entry requires its author to state the range, not anyone to infer.
UNDECLARED_BY_HISTORY: dict[str, str] = {
    "REVIEW-R3.md": "reviewed 'the seven merged units', not a range",
    "REVIEW-R4.md": "reviewed U5 at 555bad6, a tree state, not a range",
    "REVIEW-R5.md": "reviewed U6 at d0abd10, a tree state, not a range",
    "REVIEW-R6.md": "reviewed U7 at ec38835, a tree state, not a range",
    "REVIEW-R7.md": "reviewed U8/U9/U12/U10 at bc0f958, a tree state",
    "REVIEW-R8.md": "reviewed U14 at 2c6ff19, a tree state, not a range",
}


def git(*args: str) -> str:
    """Run git in the repo; return stdout, or raise with its stderr."""
    done = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True
    )
    if done.returncode != 0:
        message = f"git {' '.join(args)} failed: {done.stderr.strip()}"
        raise SystemExit(message)
    return done.stdout.strip()


def review_documents() -> list[pathlib.Path]:
    """Every code-review document, by GLOB rather than a typed list.

    `PLAN-REVIEW-*` are excluded deliberately: they review the plan,
    not merged commits, so a commit range is not a thing they could
    declare.
    """
    found = REVIEWS.glob("*REVIEW-R*.md")
    return sorted(p for p in found if not p.name.startswith("PLAN-"))


def declared_ranges() -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Each document's declared range, and the ones declaring none."""
    ranges: dict[str, tuple[str, str]] = {}
    undeclared: list[str] = []
    for path in review_documents():
        found = DECLARATION.search(path.read_text(encoding="utf-8"))
        if found:
            ranges[path.name] = (found["base"], found["head"])
        else:
            undeclared.append(path.name)
    return ranges, undeclared


def main() -> int:
    if not review_documents():
        print("MATCHED ZERO review documents. A clean result here would")
        print("mean nothing - an empty population reports full coverage.")
        return 2

    ranges, undeclared = declared_ranges()

    covered: set[str] = set()
    for name, (base, head) in sorted(ranges.items()):
        commits = git("rev-list", f"{base}..{head}").split()
        covered.update(commits)
        print(f"  DECLARED  {name}: {base}..{head} ({len(commits)} commits)")

    unexplained = [n for n in undeclared if n not in UNDECLARED_BY_HISTORY]
    for name in sorted(undeclared):
        reason = UNDECLARED_BY_HISTORY.get(name)
        if reason:
            print(f"  HISTORIC  {name}: no range - {reason}")
        else:
            print(f"  UNDECLARED {name}: no REVIEW-COVERS line, no reason")

    if not ranges:
        print("\nNo document declares a range, so nothing can be checked.")
        return 2

    # The CONTAINER: every commit on the trunk from the earliest
    # declared base to HEAD. Enumerated, never listed - the whole point.
    earliest = min(
        ranges.values(), key=lambda r: int(git("rev-list", "--count", r[0]))
    )[0]
    trunk = git("rev-list", f"{earliest}..HEAD").split()
    uncovered = [c for c in trunk if c not in covered]

    print(f"\nTrunk commits since {earliest[:7]}: {len(trunk)}")
    print(f"Inside a declared review range: {len(trunk) - len(uncovered)}")
    print(f"COVERED BY NOTHING: {len(uncovered)}")

    if uncovered:
        print("\nThe most recent 25 with no review round:")
        for sha in uncovered[:25]:
            print(f"  {git('log', '-1', '--format=%h %s', sha)[:88]}")

    if uncovered or unexplained:
        print(
            "\nA commit inside no round's declared range has been read by\n"
            "nobody. NOTE: this proves a commit falls in a declared range,\n"
            "NOT that the round read it - a declaration is a claim."
        )
        return 1

    print("\nEvery trunk commit falls inside some round's declared range.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
